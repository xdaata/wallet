import uuid
from locust import HttpUser, task, between


class WalletUser(HttpUser):
    wait_time = between(0.1, 0.5)

    user_id: int | None = None
    wallet_id: int | None = None

    def on_start(self):
        """ При старте каждого виртуального пользователя: создаем ему кошелек """
        self.user_id = uuid.uuid4().int % 100000
        response = self.client.post(
            f"/wallets/?user_id={self.user_id}",
            json={"currency": "RUB"}
        )
        if response.status_code == 200:
            self.wallet_id = response.json().get("id")
        else:
            self.wallet_id = 1

    @task(3)
    def deposit(self):
        """Пополнение с уникальным ключом"""
        if self.wallet_id:
            idempotency_key = str(uuid.uuid4())
            self.client.post(
                f"/wallets/{self.wallet_id}/deposit?amount=100.00",
                headers={"x-idempotency-key": idempotency_key}
            )

    @task(1)
    def deposit_duplicate_key(self):
        """Проверка идемпотентности (повторяющийся ключ)"""
        if self.wallet_id:
            self.client.post(
                f"/wallets/{self.wallet_id}/deposit?amount=50.00",
                headers={"x-idempotency-key": f"fixed-key-{self.wallet_id}"}
            )

    @task(2)
    def get_balance(self):
        if self.wallet_id:
            self.client.get(f"/wallets/{self.wallet_id}")