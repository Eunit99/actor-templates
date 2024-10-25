"""This module defines the main entry point for the Apify Actor.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

from apify import Actor, Request
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext


async def main() -> None:
    """Main entry point for the Apify Actor.

    This coroutine is executed using `asyncio.run()`, so it must remain an asynchronous function for proper execution.
    Asynchronous execution is required for communication with Apify platform, and it also enhances performance in
    the field of web scraping significantly.
    """
    async with Actor:
        # Retrieve the Actor input, and use default values if not provided.
        actor_input = await Actor.get_input() or {}
        start_urls = [url.get('url') for url in actor_input.get('start_urls', [{'url': 'https://apify.com'}])]

        # Exit if no start URLs are provided.
        if not start_urls:
            Actor.log.info('No start URLs specified in Actor input, exiting...')
            await Actor.exit()

        # Create a crawler.
        crawler = PlaywrightCrawler(
            # Limit the crawl to max requests. Remove or increase it for crawling all links.
            max_requests_per_crawl=50,
            headless=True,
        )

        # Define a request handler, which will be called for every request.
        @crawler.router.default_handler
        async def request_handler(context: PlaywrightCrawlingContext) -> None:
            url = context.request.url
            Actor.log.info(f'Scraping {url}...')

            # Extract the desired data.
            data = {
                'url': context.request.url,
                'title': await context.page.title(),
                'h1s': [await h1.text_content() for h1 in await context.page.locator('h1').all()],
                'h2s': [await h2.text_content() for h2 in await context.page.locator('h2').all()],
                'h3s': [await h3.text_content() for h3 in await context.page.locator('h3').all()],
            }

            # Store the extracted data to the default dataset.
            await context.push_data(data)

            # Enqueue additional links found on the current page.
            await context.enqueue_links()

        # Run the crawler with the starting requests.
        await crawler.run(start_urls)