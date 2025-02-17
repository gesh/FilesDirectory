# Project Setup Guide

## Prerequisites
- Docker 
- Docker Compose

## Getting Started

1. Clone the repository
2. Run `docker-compose build`
3. Run `docker-compose up`
4. Navigate to `http://localhost:3333` to access the application

## Project Structure

- `client`: Angular project for the frontend
- `api`: Flask project for the backend

## Running Tests

Execute the tests with `docker-compose exec api python -m pytest tests/test_app.py -v`