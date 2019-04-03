# Play

**Play** is a powerful command line Python media player over [Omxplayer](https://github.com/popcornmix/omxplayer) that allows you to play audio and video files and organize them in playlists. You can easily save these playlists ([SQLite](https://www.sqlite.org/index.html) database) to continue them later on, starting from the file where you leaved.

## Installation

    git clone https://github.com/caumons/play.git
    sudo mv play/ /opt/
    sudo ln -s /opt/play/play.py /usr/local/bin/play
    sudo chmod a+w -R /opt/play/ && sudo chmod a+x /opt/play/play.py

If you also want *play* to be available from your files browser to easily play files:

    sudo apt-get update && sudo apt-get install -y xterm
    sudo ln -s /opt/play/play.desktop /usr/share/applications/play.desktop

After doing so, you should be able to select the desired files, right button click, select "Open with", choose "Audio & video" and finally launch *play*. If the option doesn't appear, reboot your system and try again.

## Playing files

You can pass one or multiple files to play them sequentially:

    play audio.mp3 video.mp4

You can reproduce audio and video files via Internet streaming (http or https) too:

    play http://mydomain.com/audiofile https://mydomain.com/videofile

Wildcards can also be used:

    play *.mp3

You can also play files in folders. This will only play media files directly inside `folder` dir:

    play folder

You can even play files **recursively (-r, --recursive)**. This will play all media files contained in `folder` or in any subdir:

    play -r folder

By default, play will reproduce any audio or video file. You can change this behaviour too using the **type (-t, --type)** flag:

    play -t audio .  ⇐ Only audio files
    play -t video .  ⇐ Only video files
    play -t both .  ⇐ Default option. Plays audio and video files
    play -t auto .  ⇐ Uses the type from the first media file found

Of course, you can mix all these options, even with local and streaming files e.g.:

    play -r audio.mp3 video.mp4 https://mydomain.com/mediafile *.mkv folder

To play files already saved in a playlist you just need to tell *play* the list name:

    play mylist

**Important!** When playing files from a saved playlist, please, make sure that *play* starts playing the next file before you quit the program, because updating the playlist occurs at the beginning of file playback.

*Note*: Before playing video files, it's highly recommended to configure the Omxplayer `win` option. Read "Omxplayer args" and "Settings" sections below.

## Managing playback

You can *control the file playback using the same shortcuts as Omxplayer*, plus some more. In fact, it's Omxplayer the one that actually plays the media files. Here are some of the most important ones:

 - **Pause/Continue**: space bar
 - **Stop playback**: Control+c (^c). This will give you the option to play another file or quit:
     - To *exit* hit Enter or type `n` and hit Enter
     - To *play next file* type `y` and hit Enter
     - To *play another file* write its index number and hit Enter
     - To *replay current file* introduce any other value and hit Enter
 - **Next file**: ESC or `q`
 - **Forward 30 s**: right arrow
 - **Forward 10 min**: up arrow
 - **Backwards 30 s**: left arrow
 - **Backwards 10 min**: down arrow
 - For more options see Omxplayer help

## Creating playlists

To create a **new playlist (-n, --playlist)** you have to give it a name and tell *play* which are the files (local or streaming). You can use the params to find the files as explained in the section "Playing files". Here you have some examples:

    play -n playlist1 /path/to/files1/  ⇐ New audio/video playlist
    play -rn playlist2  /path/to/files2/  ⇐ New recursive audio/video playlist
    play -rn playlist3 -t audio .  ⇐ New recursive audio playlist (of current dir)
    play -rn playlist4 -t video .  ⇐ New recursive video playlist (of current dir)
    play -rn playlist5 -t auto .  ⇐ New rec. audio or video playlist (of cur. dir)

## Managing playlists

**Playlists (-p, --playlists)**: List user playlists

    play -p

**Update (-u, --update)**: Update playlist, re-reading playlist directories from disk

    play -u myplaylist

**Delete (-d, --delete)**: Delete playlist

    play -d myplaylist

**Delete all (-D, --delete-all)**: Delete all current user playlists

    play -D

## More options to play files

**Bucle (-b, --bucle)**: Starts the list from the beginning after the last file playback ends

    play -b *

**Shuffle (-s, --shuffle)**:  Plays files in a random way

    play -s *

**Limit (-l, --limit)**: Limits *play* to specified number of files

    play -l 10 *  ⇐ Plays first 10 files

**Offset (-f, --offset)**: Skips the first number of specified files

    play -f 5 *  ⇐ Skips first 5 found files

Of course, you can **combine** all or some of these options too, for example:

    play -bs -l 10 -f 5 *

You can even save the playlist resulting from the combination:

    play -bs -l 10 -f 5 -n myplaylist *

## Omxplayer args

 - **Output (-o, --output)**: Options are: hdmi, local, both. Default is both
 - **Window (-w, --window)**: First, you need to know your screen resolution. Then, set the position of video window with one of these formats:  `'x1 y1 x2 y2'` or `x1,y1,x2,y2`


## Settings

You can create a file called `settings.py` at the same directory where `play.py` lives and define the following variables to override default values:

 - `DB_PATH`: Default is `playlists.db` at *play* directory
 - `AUDIO_MOUNT_POINT` (optional): Called for audio files with `mount AUDIO_MOUNT_POINT`
 - `VIDEO_MOUNT_POINT` (optional): Called for video files with `mount VIDEO_MOUNT_POINT`
 - `OMXPLAYER_WIN` (optional): Video files only. Adjust for better display, see "Omxplayer args"
 - `EXCLUDED_FORMATS`: Tuple of excluded media formats. Defaults to: `('.m3u',)`

*Note*: You have to previously configure `/etc/fstab` to make `AUDIO_MOUNT_POINT` and `VIDEO_MOUNT_POINT` work.
