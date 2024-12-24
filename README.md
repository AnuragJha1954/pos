# POSAPI

POSAPI is a Django-based REST API for managing various aspects of a Point of Sale (POS) system. It includes features for user management, authentication, inventory control, sales tracking, and more.

## Features

- User Management: Custom user model with phone number authentication, KYC, and referral system.
- Inventory Management: CRUD operations for products and categories.
- Sales and Transactions: Create and manage sales records, track payment statuses, and generate invoices.
- Order generation and Billing management


## Getting Started

### Prerequisites

- Python 3.8+
- Django 3.2+
- Django REST Framework 3.12+
- PostgreSQL (or any preferred database)

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/posapi.git
    cd posapi
    ```


2. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up the database**:
    - Configure your database settings in `posapi/settings.py`.
    - Apply the migrations:
    ```bash
    python manage.py migrate
    ```

4. **Create a superuser**:
    ```bash
    python manage.py createsuperuser
    ```

5. **Run the development server**:
    ```bash
    python manage.py runserver
    ```

### API Documentation

POSAPI uses Django REST Framework's built-in documentation. You can access the API documentation by navigating to `/swagger/` or `/redoc/` on your local server.

### Project Structure

```
posapi/
├── posapi/              # Project settings and configuration
│   ├── settings.py      # Main settings file
│   ├── urls.py          # URL routing
│   ├── wsgi.py          # WSGI application
│   └── asgi.py          # ASGI application
├── users/               # Users app (custom user model)
├── userauth/            # User Authentication app
├── manage.py            # Django's command-line utility
└── README.md            # Project documentation
```


### Running Tests

To run tests, use the following command:

```bash
python manage.py test
```

### Deployment

For deployment, ensure that you:

- Set `DEBUG` to `False`.
- Configure your server (e.g., using Gunicorn, Nginx).
- Set up a secure SSL connection.
- Use environment variables to manage sensitive information.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

## License

This project is licensed under the BSD 3-Clause License - see the LICENSE file for details.

## Contact

For any inquiries, feel free to contact us at [sales@vibrantdigitech.com](mailto:sales@vibrantdigitech.com).
