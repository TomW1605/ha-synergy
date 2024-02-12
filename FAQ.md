# FAQ

## Q. Why "X" doesn't work

A. Most features in this integration are experimental. If it's not listed as supported it's **not** supported. Double-check this.

## Q. Historical sensors (consumption and generation) doesn't have a value

A. They are not supposed to. Historical sensors are a hack, HomeAssistant is not supposed to have historical sensors.

Historical sensors can't provide the current state, Home Assistant will show "undefined" state forever, it's OK and intentional. To view historical data you have to go [History](https://my.home-assistant.io/redirect/history/) → Select any historical sensor →  Go back some days.

Keep in mind that historical data has a ~24-48h delay.
