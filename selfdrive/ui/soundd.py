import numpy as np
import wave

from typing import Dict, Optional, Tuple

from cereal import car, messaging
from openpilot.common.basedir import BASEDIR

SAMPLE_RATE = 48000

AudibleAlert = car.CarControl.HUDControl.AudibleAlert

MAX_VOLUME = 1.0

sound_list: Dict[int, Tuple[str, Optional[int], float]] = {
  # AudibleAlert, file name, play count (none for infinite)
  AudibleAlert.engage: ("engage.wav", 1, MAX_VOLUME),
  AudibleAlert.disengage: ("disengage.wav", 1, MAX_VOLUME),
  AudibleAlert.refuse: ("refuse.wav", 1, MAX_VOLUME),

  AudibleAlert.prompt: ("prompt.wav", 1, MAX_VOLUME),
  AudibleAlert.promptRepeat: ("prompt.wav", None, MAX_VOLUME),
  AudibleAlert.promptDistracted: ("prompt_distracted.wav", None, MAX_VOLUME),

  AudibleAlert.warningSoft: ("warning_soft.wav", None, MAX_VOLUME),
  AudibleAlert.warningImmediate: ("warning_immediate.wav", None, MAX_VOLUME),
}

loaded_sounds: Dict[int, np.ndarray] = {}

# Load all sounds
for sound in sound_list:
  filename, play_count, volume = sound_list[sound]

  wavefile = wave.open(BASEDIR + "/selfdrive/assets/sounds/" + filename, 'r')

  assert wavefile.getnchannels() == 1
  assert wavefile.getsampwidth() == 2
  assert wavefile.getframerate() == SAMPLE_RATE

  length = wavefile.getnframes()
  sound_data = np.frombuffer(wavefile.readframes(length), dtype=np.int16).astype(np.float32) / 32767

  loaded_sounds[sound] = sound_data


def main():
  import sounddevice as sd
  sm = messaging.SubMaster(['controlsState', 'microphone'])

  current_alert = AudibleAlert.none
  current_alert_looped = 0
  current_volume = MAX_VOLUME

  with sd.OutputStream(channels=1, samplerate=SAMPLE_RATE) as stream:
    while True:
      sm.update(timeout=1000)

      if sm.updated['controlsState']:
        new_alert = sm['controlsState'].alertSound.raw
        if current_alert != new_alert:
          current_alert = new_alert
          current_alert_looped = 0

      if sm.updated['microphone']:
        current_volume = (sm["microphone"].soundPressureWeightedDb - 30) / 30

      if current_alert != AudibleAlert.none:
        num_loops = sound_list[current_alert][1]
        if num_loops is None or current_alert_looped < num_loops:
          stream.write(loaded_sounds[current_alert] * current_volume)
          current_alert_looped += 1


if __name__ == "__main__":
  main()