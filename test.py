import asyncio
from crawl4ai import AsyncWebCrawler
import json


async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        # js_code = [
        #     "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"
        # ]
        result = await crawler.arun(
            url="https://www.classcentral.com/course/game-theory-1-308",
            # js_code=js_code,
            # css_selector=".wide-tease-item__description",
            css_selector=".bg-white.medium-up-padding-large.border-bottom.medium-up-border-all.border-gray-light.medium-up-radius-small.margin-bottom-medium.relative",
            bypass_cache=True,
            extract_with_tags=True,
        )
        # print(result.extracted_content)
        json.dump(json.loads(result.extracted_content), open("s.json", "w"))


if __name__ == "__main__":
    asyncio.run(main())
