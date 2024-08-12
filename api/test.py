import aiohttp
import asyncio

# The number of requests you want to send
NUM_REQUESTS = 1000


async def send_request(session, url):
    async with session.get(url) as response:
        status = response.status
        content = await response.json()
        return status, content


async def run_load_test(url, num_requests):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(num_requests):
            tasks.append(send_request(session, url))
        responses = await asyncio.gather(*tasks)
        for status, content in responses:
            print(f"Status: {status}, Response: {content}")


if __name__ == "__main__":
    url = "http://localhost:8000/api/youtube-transcription?video_id=iR2O2GPbB0E"

    # Run the load test
    asyncio.run(run_load_test(url, NUM_REQUESTS))
