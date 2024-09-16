import aiohttp
import asyncio
import argparse
from datetime import datetime, timedelta


async def get_exchange_rates_for_date(session, date):
    formatted_date = date.strftime("%d.%m.%Y")
    url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={formatted_date}"
    print(f"Запит до URL: {url}")

    try:
        async with session.get(url) as response:
            if response.status == 200:
                result = await response.json()
                return {formatted_date: result}
            else:
                print(f"Failed to fetch data from {url}: {response.status}")
                return {formatted_date: None}
    except aiohttp.ClientConnectorError as exc:
        print(f"Failed to connect to {url}: {exc}")
        return {formatted_date: None}


def filter_curr(data, currencies):
    filtered_data = {}
    for date, info in data.items():
        if info:
            filtered_rates = {}
            for rate in info.get('exchangeRate', []):
                if 'currency' in rate and rate['currency'] in currencies:
                    filtered_rates[rate['currency']] = rate
            if filtered_rates:
                filtered_data[date] = {
                    'exchangeRate': filtered_rates
                }
    return filtered_data


async def get_exchange_rates(days_back):
    today = datetime.now()

    async with aiohttp.ClientSession() as session:
        tasks = []

        for i in range(days_back):
            target_date = today - timedelta(days=i)
            tasks.append(get_exchange_rates_for_date(session, target_date))

        results = await asyncio.gather(*tasks)

        data = {}
        for result in results:
            data.update(result)
        return filter_curr(data, ["USD", "EUR"])


async def main():
    parser = argparse.ArgumentParser(description="Програма для отримання курсів валют")
    parser.add_argument("days", type=int, help="Кількість днів для отримання даних")

    args = parser.parse_args()

    if 1 <= args.days <= 10:
        results = await get_exchange_rates(args.days)

        for date, info in results.items():
            print(f"Курси валют на {date}:")
            for currency, rate in info.get('exchangeRate', {}).items():
                print(f"{currency}: {rate}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        print(f"Error: {e}")
