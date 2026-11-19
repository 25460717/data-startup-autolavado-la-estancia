from locust import HttpUser, task, between

class UsuarioAutolavado(HttpUser):
    wait_time = between(1, 2)

    @task(3)
    def consultar_pronostico(self):
        self.client.get("/pronostico?dias=7")

    @task(1)
    def clasificar_cliente(self):
        self.client.post("/clasificar", json={"dia_semana": 5, "hora": 14, "es_quincena": 1})
