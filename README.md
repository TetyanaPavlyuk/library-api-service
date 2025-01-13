# Library API

> RESTful API for a library written in DRF 

## Description

### The API allows users to:
- register with their email and password to create an account,
- login with their credentials and receive a token for authentication,
- browse (for not authenticated users also) and borrow all books,
- create and view all their borrowings,
- return borrowing,
- create and view all their payments.

### Additionally, the API allows admin users to:
- create, update and delete books,
- view a list of all users,
- view a list of all borrowings,
- search for borrowing by `is_active` or `user_id` parameter,
- view a list of all payments.

When a user creates a Borrowing, the system automatically initiates a payment request for the borrowing fee.
If during returning Borrowing, the actual_return_date is greater 
than the expected_return_date - create request to pay fine for user (FINE_MULTIPLIER 
is defined in .env file - for ex. 2).
A user cannot borrow new books if they have at least one pending payment.

Sending notifications to the telegram channel: 
- on each new Borrowing creation,
- about each overdue (check every day),
- on each successful Payment with its details.

## Getting Started

### Installing using GitHub

```shell
git clone https://github.com/TetyanaPavlyuk/library-api-service.git
cd library_api_service
```

### Run with Docker

Copy `.env.sample` to `.env`:
```shell
cp .env.sample .env
```
Populate the .env file with the required environment variables.

Build and run the containers
```shell
docker-compose build
docker-compose up
```

Run tests
```shell
docker-compose exec library python manage.py test
```

### Getting Access

Create superuser
```shell
docker-compose exec library python manage.py createsuperuser
```
Get access token via /api/library/users/token/

## Features

* JWT authenticated
* Admin panel /admin/
* Documentation is located at /api/library/schema/swagger-ui/
* Celery and Redis for check overdue borrowings daily
* Notifications into telegram channel
* Stripe Payment Sessions

