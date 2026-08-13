"""LA BASE 2026 ES SAGRADA: si su hash cambia sin ceremonia, el CI grita.
Para actualizarla legitimamente (nueva base anual): regenerar el .sha256 en el MISMO commit."""
import hashlib, os, sys
raiz = os.path.join(os.path.dirname(__file__), '..', 'app', 'data')
actual = hashlib.sha256(open(os.path.join(raiz, 'apu_2026.json'), 'rb').read()).hexdigest()
sellado = open(os.path.join(raiz, 'apu_2026.sha256')).read().strip()
if actual != sellado:
    print(f"❌ LA BASE 2026 FUE MODIFICADA\n   sellado: {sellado}\n   actual:  {actual}")
    sys.exit(1)
print("OK: base 2026 intacta (hash verificado)")
