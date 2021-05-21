# TeleMovieDL

A Telegram bot that will fetch any movie you tell it to, and download it for you to watch on Plex or *something else?*.

This is my first time making a Telegram bot, and also my first time using docker :)

This release is probably a bit buggy, I coded this in a few hours just for my use but people wanted to use it so yeah :)
I'll be updating this, adding more error handling, making the code much less messy, and adding some more features ;) *(tv shows.....)*

## How to run

Using docker is probably the easiest way.  [Make sure you have docker installed](https://docs.docker.com/get-docker/).

Setup transmission-daemon, you can use [this link](https://linuxconfig.org/how-to-set-up-transmission-daemon-on-a-raspberry-pi-and-control-it-via-web-interface) to help.

Clone this repository `git clone https://github.com/sexnine/tele-movie-dl.git`

Navigate into the repository `cd tele-movie-dl/`

Make a copy of `config.example.yml` as `config.yml` using `cp config.example.yml config.yml`

Edit the config file with your Telegram bot token, transmission-daemon credentials, and the IDs of the users you want to be able to use your bot.  (You can get your Telegram ID by running the container and running the `/movie` command, it will log the ID that tried to use that command.  You can then put that ID in your config and rebuild the container.)

Build the docker container `docker build -t tele-movie-dl`

Run the docker container `docker run -d tele-movie-dl`

## Contributing

If you would like to contribute, please feel free to message me prior on Discord: `sexnine#6969` :)

## License

MIT License

Copyright (c) 2021 sexnine

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

**Note: This is for educational purposes only.  Do not use this tool to obtain any content you do not have the rights to.**
