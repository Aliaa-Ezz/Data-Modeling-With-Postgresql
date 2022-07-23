import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *

"""
Reading the Songs rows from songs JSON file to be able to insert the data in the table we made for the songs
and artists as well.
we are reading the data as a list and only the first row of values.

    INPUTS: 
    * cur the cursor variable
    * filepath the file path to the song file
"""
def process_song_file(cur, filepath):
    # open song file
    df = pd.read_json(filepath, lines=True)

    # insert song record
    song_data = df[['song_id', 'title', 'artist_id', 'year','duration']].values[0]
    cur.execute(song_table_insert, song_data)
    
    # insert artist record
    artist_data = df[['artist_id', 'artist_name','artist_location', 'artist_latitude', 'artist_longitude']].values[0]
    cur.execute(artist_table_insert, artist_data)

"""
From the logs file, we will get the data from the JSON files to fill the time, users and then we will insert all the data extracted to song play table

    INPUTS: 
    * cur the cursor variable
    * filepath the file path to the log file
"""
def process_log_file(cur, filepath):
    # open log file
    df = pd.read_json(filepath, lines=True)

    # filter by NextSong action
    df = df.loc[df['page'] == 'NextSong']

    # convert timestamp column to datetime
    t = pd.to_datetime(df['ts'], unit = 'ms')
    
    # insert time data records
    time_data = (t, t.dt.hour.values, t.dt.day.values, t.dt.weekofyear.values, t.dt.month.values,t.dt.year.values, t.dt.weekday.values)
    column_labels = ('start_time', 'hour' , 'day', 'week', 'month', 'year', 'weekday')
    time_df = pd.DataFrame(dict(zip(column_labels, time_data)))

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = df[['userId', 'firstName', 'lastName','gender','level']]

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    for index, row in df.iterrows():
        
        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        songplay_data = [row.ts, row.userId, row.level, songid,artistid, row.sessionId, row.location, row.userAgent]
        cur.execute(songplay_table_insert, songplay_data)
"""
getting all the data related to songs and each other table from the JSON files of Song and Log file

    INPUTS: 
    * cur the cursor variable
    * filepath the file path to the song file
    * conn the Connection to our database
    * func function for the processing of each file
    
"""

def process_data(cur, conn, filepath, func):
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))

"""
Finally, to the main funtion that we call all the previous magic
first, we start our database connection
getting our cursor set
processing the data for each file.
"""

def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()