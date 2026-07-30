"""Efeitos sonoros do terminal — opcionais, desligáveis nos ajustes.

A CLI usava `winsound.Beep`, que **bloqueia** a thread até o som acabar. Numa
interface gráfica isso travaria a animação a cada caractere digitado. Aqui os
tons são sintetizados como WAV em memória e tocados com
`PlaySound(SND_ASYNC | SND_MEMORY)`, que retorna na hora.

Windows-only, como o resto do projeto. Em qualquer falha o som simplesmente não
toca — nunca derruba a interface.
"""

import io
import math
import struct
import wave

try:
    import winsound
except ImportError:  # pragma: no cover - fora do Windows
    winsound = None

SAMPLE_RATE = 22050


def _tone(frequency, milliseconds, volume=0.35, fade_ms=4):
    """Sintetiza um WAV mono de 16 bits com uma onda senoidal.

    O `fade_ms` nas pontas evita o "clique" que uma onda cortada no meio do
    ciclo produz — bem audível quando os tons se repetem rápido.
    """
    total = int(SAMPLE_RATE * milliseconds / 1000)
    fade = max(1, int(SAMPLE_RATE * fade_ms / 1000))
    frames = bytearray()

    for i in range(total):
        envelope = min(1.0, i / fade, (total - i) / fade)
        value = math.sin(2 * math.pi * frequency * i / SAMPLE_RATE)
        frames += struct.pack("<h", int(value * envelope * volume * 32767))

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(bytes(frames))
    return buffer.getvalue()


class SoundPlayer:
    """Banco de efeitos do terminal.

    Os tons são gerados uma vez, sob demanda, e ficam em cache: sintetizar a
    cada tecla custaria mais que tocar.
    """

    # nome -> (frequência Hz, duração ms, volume)
    EFFECTS = {
        "key": (1400, 16, 0.22),      # digitação (a CLI usava Beep(1400, 20))
        "scramble": (620, 12, 0.14),  # decodificação em andamento
        "confirm": (990, 90, 0.30),   # acesso concedido
        "deny": (180, 180, 0.30),     # entrada recusada
        "boot": (440, 120, 0.25),     # início da abertura
    }

    def __init__(self, enabled=False):
        self.enabled = enabled
        self._cache = {}

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)

    def play(self, name):
        if not self.enabled or winsound is None:
            return
        try:
            data = self._cache.get(name)
            if data is None:
                spec = self.EFFECTS.get(name)
                if spec is None:
                    return
                frequency, duration, volume = spec
                data = self._cache[name] = _tone(frequency, duration, volume)
            # SND_ASYNC devolve o controle imediatamente; um som novo substitui o
            # anterior, que é justamente o efeito de "matraca" de terminal.
            winsound.PlaySound(data, winsound.SND_MEMORY | winsound.SND_ASYNC)
        except Exception:
            # Placa de som ausente, driver reclamando, buffer inválido: silencia.
            pass

    def stop(self):
        if winsound is None:
            return
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
