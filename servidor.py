# Servidor local para la extensión DIS para Forma  (v2)
# - Atiende varias conexiones a la vez: Chrome abre conexiones "de reserva" que dejaban
#   colgado al servidor anterior, y por eso Forma ya no cargaba el panel.
# - Prohíbe al navegador guardar copias viejas del panel.
# - Los cortes de conexión del navegador (WinError 10053) se reportan en una línea, sin traceback.
# Uso: abre una terminal en esta carpeta y ejecuta   py servidor.py
import http.server, os, socket, sys

PUERTO = 5173
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class SinCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Expires", "0")
        super().end_headers()

class Servidor(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    def server_bind(self):
        # IPv6 + IPv4 en el mismo puerto, para que "localhost" responda por cualquiera de los dos
        if self.address_family == socket.AF_INET6:
            try: self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            except OSError: pass
        super().server_bind()
    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)):
            print("  · el navegador cerró una conexión antes de terminar (normal al recargar o cerrar el panel)")
            return
        super().handle_error(request, client_address)

class Servidor6(Servidor):
    address_family = socket.AF_INET6

def arrancar():
    try:
        return Servidor6(("::", PUERTO), SinCache)
    except OSError:
        pass
    try:
        return Servidor(("", PUERTO), SinCache)
    except OSError as e:
        print(f"No se pudo abrir el puerto {PUERTO}: {e}")
        print("Probablemente otro servidor sigue abierto en otra terminal. Ciérralo (Ctrl+C) y vuelve a intentar.")
        sys.exit(1)

if __name__ == "__main__":
    srv = arrancar()
    print(f"DIS para Forma en http://localhost:{PUERTO}  (Ctrl+C para detener)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
