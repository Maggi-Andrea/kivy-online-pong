"""
An example of periodically scheduling coroutines using an infinite loop of
awaiting and sleeping.
"""

import asyncio
import argparse
import logging
from datetime import datetime
from functools import partial
from random import randint

import aiohttp
import async_timeout


LOGGER_FORMAT = '%(asctime)s %(message)s'
URL_TEMPLATE = "https://hacker-news.firebaseio.com/v0/item/{}.json"
TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
FETCH_TIMEOUT = 10

parser = argparse.ArgumentParser(
    description='Calculate the number of comments of the top stories in HN.')
parser.add_argument(
    '--period', type=int, default=5, help='Number of seconds between poll')
parser.add_argument(
    '--limit', type=int, default=5,
    help='Number of new stories to calculate comments for')
parser.add_argument('--verbose', action='store_true', help='Detailed output')


logging.basicConfig(format=LOGGER_FORMAT, datefmt='[%H:%M:%S]')
log = logging.getLogger()
log.setLevel(logging.INFO)

fetch_counter = 0

MAXIMUM_FETCHES = 25


class BoomException(Exception):
    pass


class URLFetcher:
    """Provides counting of URL fetches for a particular task.
    """

    def __init__(self):
        self.fetch_counter = 0

    async def fetch(self, session, url):
        """Fetch a URL using aiohttp returning parsed JSON response.
        As suggested by the aiohttp docs we reuse the session.
        """
        with async_timeout.timeout(FETCH_TIMEOUT):
            if self.fetch_counter > MAXIMUM_FETCHES:
                raise BoomException('BOOM!')
            # elif randint(0, 10) == 0:
            #     raise Exception('Random generic exception')
            async with session.get(url) as response:
                self.fetch_counter += 1
                response = await response.json()
                return response


async def post_number_of_comments(loop, session, fetcher, post_id, iteration):
    """Retrieve data for current post and recursively for all comments.
    """
    url = URL_TEMPLATE.format(post_id)
    try:
        log.info(f"Retrieving post {post_id} - ({iteration})")
        response = await fetcher.fetch(session, url)
    except Exception as e:
        log.error(f"Error retrieving post {post_id}: {e} - ({iteration})")
        raise e
    if 'kids' not in response:  # base case, there are no comments
        return 0

    log.info(f"Retrieved post {post_id} - ({iteration})")

    # calculate this post's comments as number of comments
    number_of_comments = len(response['kids'])

    try:
        # create recursive tasks for all comments
        tasks = [asyncio.ensure_future(post_number_of_comments(loop, session, fetcher, kid_id, iteration))
                 for kid_id in response['kids']]
        # schedule the tasks and retrieve results
        try:
            results = await asyncio.gather(*tasks)
        except Exception as e:
            log.error(f"Error for post {post_id} with {e} - ({iteration})")
            raise

        # reduce the descendents comments and add it to this post's
        number_of_comments += sum(results)
        log.debug(f'{post_id:^6} > {number_of_comments} comments - ({iteration})')

    except asyncio.CancelledError:
        if tasks:
            log.info(f"Comments for post {post_id} cancelled, cancelling {len(tasks)} child tasks- ({iteration})")
            for task in tasks:
                task.cancel()
        else:
            log.info(f"Comments for post {post_id} cancelled - ({iteration})")

    return number_of_comments


async def get_comments_of_top_stories(loop, limit, iteration):
    """Retrieve top stories in HN.
    """
    async with aiohttp.ClientSession(loop=loop) as session:
        fetcher = URLFetcher()
        try:
            log.info(f"Retrieving top stories - ({iteration})")
            response = await fetcher.fetch(session, TOP_STORIES_URL)
        except Exception as e:
            log.error(f"Error retrieving top stories: {e} - ({iteration})")
            raise

        log.info(f"Retrieved top stories {response[:limit]}- ({iteration})")

        tasks = {
            asyncio.ensure_future(
                post_number_of_comments(loop, session, fetcher, post_id, iteration)
            ): post_id for post_id in response[:limit]}

        # return on first exception to cancel any pending tasks
        done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_EXCEPTION)

        # if there are pending tasks is because there was an exception
        # cancel any pending tasks
        for pending_task in pending:
            pending_task.cancel()

        # process the done tasks
        for done_task in done:
            try:
                log.info(f"Post {tasks[done_task]} has {done_task.result()} comments - ({iteration})")
            except Exception as e:
                log.info(f"Error retrieving comments for top stories: {e} - ({iteration})")
        return fetcher.fetch_counter  # return the fetch count


def poll_top_stories_for_comments(loop, period, limit, iteration=0):
    """Periodically poll for new stories and retrieve number of comments.
    """

    log.info(f"Calculating comments for top {limit} stories. - ({iteration})")

    future = asyncio.ensure_future(get_comments_of_top_stories(loop, limit, iteration))

    now = datetime.now()

    def callback(fut):
        try:
            fetch_count = fut.result()
        except BoomException as e:
            log.error(f"BoomException something went {e}. - ({iteration})")
            return
        except Exception as e:
            log.error(f"Something went {str(e)}. - ({iteration})")
            return
        log.info(
            f"> Calculating comments took {(datetime.now() - now).total_seconds():.2f} seconds "
            f"and {fetch_count} fetches - ({iteration})")

    future.add_done_callback(callback)

    log.info(f"Waiting for {period} seconds... - ({iteration})")

    iteration += 1
    loop.call_later(
        period,
        partial(  # or call_at(loop.time() + period)
            poll_top_stories_for_comments,
            loop, period, limit, iteration
        )
    )


if __name__ == '__main__':
    args = parser.parse_args()
    if args.verbose:
        log.setLevel(logging.DEBUG)

    loop = asyncio.get_event_loop()
    poll_top_stories_for_comments(loop, args.period, args.limit)

    loop.run_forever()
    loop.close()
