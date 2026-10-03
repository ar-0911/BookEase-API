# BookEase API

A seat-booking REST API with demand-based pricing, built with Flask and SQLAlchemy and packaged as a Docker image.

Full request/response examples: [Postman documentation](https://documenter.getpostman.com/view/29476665/2s9Y5eLdxh)

## Features

- **Seat inventory** across 500 seats in 10 seat classes, stored in SQLite
- **Dynamic pricing**: each class has a min, normal and max price, chosen by how full that class is (under 40% booked, 40–60%, over 60%), with a fallback when a price tier is missing
- **Multi-seat bookings** in a single request, rejected if any seat is already taken or doesn't exist
- **Email confirmation** over SMTP with the booking ID and seats
- **Booking lookup** by phone number

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/seats` | All seats, ordered by class, with `is_booked` |
| `GET` | `/seats/<id>` | One seat with its current price |
| `POST` | `/booking?id=1,2&name=…&phone=…&email=…` | Book one or more seats; returns booking ID and total |
| `GET` | `/bookings?userIdentifier=<phone>` | Seats booked under a phone number |

## Run it

```bash
cd flurn
docker build -t bookease-api .
docker run -p 5000:5000 \
  -e SMTP_USER=you@example.com \
  -e SMTP_PASSWORD=your-app-password \
  bookease-api
```

Or locally with Pipenv: `pipenv install && SMTP_USER=… SMTP_PASSWORD=… pipenv run python dbs.py`.

## Stack

Python 3.10 · Flask 2.3 · Flask-SQLAlchemy · SQLite · Docker
