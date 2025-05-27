from app.adapters.rabbitmq_config import RabbitMQConfig


def test_rabbitmq_config_default_values() -> None:
    """Tests that RabbitMQConfig initializes with correct default values."""
    config = RabbitMQConfig()
    assert config.host == "localhost"
    assert config.port == 5672
    assert config.username is None
    assert config.password is None
    assert config.virtual_host == "/"


def test_rabbitmq_config_custom_values() -> None:
    """Tests that RabbitMQConfig correctly assigns custom values."""
    custom_host = "testhost.internal"
    custom_port = 12345
    custom_username = "testuser"
    custom_password = "testpassword"
    custom_virtual_host = "/testvhost"

    config = RabbitMQConfig(
        host=custom_host,
        port=custom_port,
        username=custom_username,
        password=custom_password,
        virtual_host=custom_virtual_host,
    )

    assert config.host == custom_host
    assert config.port == custom_port
    assert config.username == custom_username
    assert config.password == custom_password
    assert config.virtual_host == custom_virtual_host


def test_rabbitmq_config_partial_custom_values() -> None:
    """Tests that RabbitMQConfig handles a mix of custom and default values."""
    custom_host = "anotherhost"
    custom_port = 5673

    config = RabbitMQConfig(host=custom_host, port=custom_port)

    assert config.host == custom_host
    assert config.port == custom_port
    assert config.username is None  # Should remain default
    assert config.password is None  # Should remain default
    assert config.virtual_host == "/"  # Should remain default
