# Technical Test

## First step
To build the app, execute this command in your terminal, in the project path:
```bash
docker-compose up --build
```

## Run the app
To run the app, execute this command in your terminal, in the project path:
```bash
docker-compose up
```

## Run tests
To run tests, execute this command in your terminal, in the project path:
```bash
docker-compose run api pytest
```

## Call the API with Insomnia
You can import the file `Insomnia` into Insomnia.

## API routes
### Create a user:
```bash
curl --request POST \
  --url http://localhost:8081/users \
  --header 'Content-Type: application/json' \
  --data '{
	"email": "email19@email.com",
	"password": "password"
}'
```

A validation code is displayed in the worker logs
To confirm your email, send this code at this route:
```bash
curl --request POST \
  --url http://localhost:8081/users/validation \
  --header 'Authorization: Basic <CREDENTIALS>' \
  --header 'Content-Type: application/json' \
  --data '{
	"validation_code": <YOUR_CODE>
}'
```
`<CREDENTIALS>` is composed with the registered email and password.
