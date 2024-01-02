import board
import busio
from telegram.ext import CommandHandler
from telegram.ext import Updater

update = Updater(token='<TOKEN>')

import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, ADS.P1)

# Create differential input between channel 0 and 1
# chan = AnalogIn(ads, ADS.P0, ADS.P1)


def main():
    """main function starts"""
    dp = update.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('voltage', voltage))
    dp.add_handler(CommandHandler('current', current))

    update.start_polling()
    update.idle()


def get_voltage(voltage_val):
    adc_voltage = round(float(voltage_val), 3)
    voltage = str(adc_voltage)
    return voltage


def start(bot, update):
    "sending the initial message to our bot when it starts"
    update.message.reply_text('Welcome to the Motor Monitor IoT bot')


def voltage(bot, update):
    voltage = get_voltage(chan.voltage)
    bot.send_message(chat_id=update.message.chat_id, text=voltage)


def current(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=motorvoltage)


if __name__ == '__main__':
    main()
