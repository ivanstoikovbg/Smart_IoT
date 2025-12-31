from machine import Pin, ADC
import config


class MQ2Sensor:
    def __init__(self, adc_pin=config.MQ2_ADC_PIN, samples=config.MQ2_SAMPLES):
        self._samples = int(samples)
        self._adc = ADC(Pin(adc_pin))
        self._adc.atten(ADC.ATTN_11DB)

    def read_avg(self):
        s = 0
        for _ in range(self._samples):
            s += self._adc.read()
        return int(s / self._samples)