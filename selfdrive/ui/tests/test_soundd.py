import pytest
import time

from cereal import messaging, car
from openpilot.selfdrive.test.helpers import with_processes


AudibleAlert = car.CarControl.HUDControl.AudibleAlert


@pytest.mark.skip
@with_processes(["soundd"])
def test_soundd():
  """Cycles through all sounds for 5 seconds each."""
  time.sleep(2)

  pm = messaging.PubMaster(['controlsState', 'microphone'])

  sound_to_play = [AudibleAlert.engage, AudibleAlert.disengage, AudibleAlert.refuse, AudibleAlert.prompt, \
                   AudibleAlert.promptRepeat, AudibleAlert.promptDistracted, AudibleAlert.warningSoft, AudibleAlert.warningImmediate]

  SOUND_PLAY_TIME = 2

  for i in range(len(sound_to_play)):
    def send_sound(sound, play_time, weighted_sound=45):
      play_start = time.monotonic()
      while time.monotonic() - play_start < play_time:
        m1 = messaging.new_message('controlsState')
        m1.controlsState.alertSound = sound

        m2 = messaging.new_message('microphone')
        m2.microphone.filteredSoundPressureWeightedDb = weighted_sound

        pm.send('controlsState', m1)
        pm.send('microphone', m2)
        time.sleep(0.01)

    for ambient_sound_level in [20, 30, 40, 50, 60, 70]:
      print(f"Testing {sound_to_play[i]} at {ambient_sound_level} dB")
      send_sound(AudibleAlert.none, 1) # 1 second gap between sounds
      send_sound(sound_to_play[i], SOUND_PLAY_TIME, ambient_sound_level)


if __name__ == "__main__":
  test_soundd()