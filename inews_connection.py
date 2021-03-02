# Property Of The British Broadcasting Corporation 2020 - Oliver Mardle.

from ftplib import FTP
import re
import datetime
import json
import os
import itertools
from itertools import cycle

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def generate_json(path, filename):
    with open("/Users/joseedwa/PycharmProjects/xyz/aws_creds.json") as aws_creds:
        inews_details = json.load(aws_creds)
        user = inews_details[1]['user']
        passwd = inews_details[1]['passwd']
        ip = inews_details[1]['ip']

    # Open FTP connection
    ftp = FTP(ip)
    ftp.login(user=user, passwd=passwd)

    # Retrieve rundown using 'path' parameter passed when function is called
    # e.g. ftp.cwd("CTS.TX.0600")
    ftp.cwd(path)

    # Store file names from rundown in list named 'lines'
    lines = ftp.nlst()

    # This loop cycles through 'lines', prefixes with the directory 'story/' and opens it silently in a text editor.
    # It then runs a retrieve command on the FTP connection using the name stored in 'line' and writes the contents
    # to the open text file and closes it.
    #
    for line in lines:

        with open("story/" + line, "wb") as story:
            ftp.retrbinary("RETR " + line, story.write)
        story.close()


    # Close FTP connection
    ftp.quit()

    # New empty list called 'data'
    data = []

    # This large loop is the bulk of the script. In a nutshell it:
    # 1) Creates an empty dictionary
    # 2) Checks to see if each row/line is floated or a break item (for line colouring later)
    # 3) Removes unnecessary data and cleans it into a more readable format
    # 4) It then takes the ID (e.g. page #)and its contents and stores them as new key & values within the dictionary
    # 5) Then it tidies the timing names into a more workable format.
    # 6) The time data comes in as seconds from midnight, e.g. 21600, we convert it to minutes & seconds for readability
    # 7) Adds the dictionary to a list
    # 8) Remove downloaded files from story directory to make space for the next load to be downloaded

    for line in lines:
        # Open local story file using the name stored in 'line'. Open in read mode 'rb'
        with open("story/" + line, "rb") as story:
            # 1) Create empty dictionary called storyLine
            storyline = {}
            # Create variable called 'copy', set its variable to False
            copy = False
            # Increment through every line in story file that was previously opened
            for row in story:
                storyline["focus"] = "false"

                # 2) If statement that checks if 'float' is in 'meta' line of story. Plus it decodes line from bytes and
                # and strips off any new line characters that may be present
                if "float" in (row.decode()).strip() and "<meta" in (row.decode()).strip():
                    # If True it adds 'floated' key to 'storyLine' dictionary and sets its value it value to True
                    storyline["floated"] = "true"
                # Checks if 'float' is not in 'meta' line of story.
                elif "float" not in (row.decode()).strip() and "<meta" in (row.decode()).strip():
                    # Set 'floated' to False if so
                    storyline["floated"] = "false"

                # Check if 'break' is in 'meta' line of story.
                if "break" in (row.decode()).strip() and "<meta" in (row.decode()).strip():
                    # Set to True if so
                    storyline["break"] = "true"
                elif "break" not in (row.decode()).strip() and "<meta" in (row.decode()).strip():
                    # False if not
                    storyline["break"] = "false"



                # Extract the first part of story id to be used as a unique ID in the app
                if "<storyid>" in (row.decode()).strip():
                    result = re.search('<storyid>(.*)</storyid>', (row.decode()).strip())
                    sep = ':'
                    stripped = result.group(1).split(sep, 1)[0]

                    storyline["story_id"] = stripped


                # 3) Looks at current line in story file and checks for 'field'
                if (row.decode()).strip() == "<fields>":
                    # If found, copy = True. Copy controls whats added to the storyLine dictionary. In this case
                    # Everything between "<fields>" and "</fields>"
                    copy = True
                    # OMIT?
                    continue

                elif (row.decode()).strip() == "</fields>":
                    copy = False
                    continue

                # If copy = True makes a new variable called decoded_line and stores current line,
                # decoded abd stripped, inside
                elif copy:
                    decoded_line = (row.decode()).strip()

                    # 3) New variable named entry which is a regular expression used to pull ID & data from decoded_line

                    entry = re.search("<f id=(.*)>(.*)</f>", decoded_line)

                    # 4) Two new variables named key and value. Key is taking the first bit of data(ID) from the first
                    # set of parentheses on line above, value is taking data from the second set of parentheses above
                    key = entry.group(1)
                    value = entry.group(2)

                    # 5) Tidy up - to make time names more uniformed
                    # If 'total-time uec' is found as a key
                    if key == "total-time uec":
                        # Key is changed to 'totaltime'
                        key = "totaltime"
                        # Adds new dictionary key, value to storyLine
                        storyline[key] = value
                    # Same as above removing '-' from back-time
                    if "back-time" in key:
                        key = "backtime"
                        # Adds new dictionary key, value to storyLine
                        storyline[key] = value

                    if "total-time" in key:
                        key = 'totaltime'
                        storyline[key] = value


                    if "page-number" in key:
                        key = "page"
                        # Adds new dictionary key, value to storyLine
                        storyline[key] = value


                    # Reduce slug/title field to 30 characters or less
                    if key == "title":
                        if len(value) >= 30:
                            value = (value[:30] + "...")
                            # print(value)

                    # Reduce format field to 20 characters or less
                    if key == "format":
                        if len(value) >= 20:
                            value = (value[:20] + "...")
                            # print(value)


                    # length_key = len(key[0])
                    # print(length_key)
                    # print(key[3])

                    # 6) Check if 'time' is within key, excluding 'backtime'
                    if "time" in key and key != "backtime":
                        # Try/except because not all times are present
                        # In every instance it tries to convert seconds to minutes and seconds e.g. :05:12
                        try:
                            storyline[key] = datetime.datetime.fromtimestamp(int(value)).strftime("%M:%S")
                        # If it fails, write empty string
                        except:
                            storyline[key] = ""

                    # Else write key and value as they are
                    else:
                        storyline[key] = value

        # 7) Append storyLine dictionary to 'data' list
        data.append(storyline)

        # Close story file
        story.close()

        # 8) Deletes the file we just read as it's no longer needed
        os.remove("story/" + line)

    # Now for the complicated task of filling in the crucial 'backtime' field of iNews.
    # The only time data that comes in from FTP is an occasional hard-out time and the total time of each line - so in
    # order for each line to have a populated backtime field we need to run some calculations.
    # The best way to visualise how we do this is to consider two columns: TOTAL and BACKTIME, we set
    # the last hard-out time into the last backtime field at the bottom of the rundown, working in reverse we then
    # subtract each total time from the previous backtime to populate the current backtime field.
    #
    # It is complicated and involves reversing the order of the list a couple of times along with
    # converting to and from seconds to hours:minutes:secs format - but so far it seems robust and it's producing
    # consistently correct backtimes.

    # Creates four new list variables ('times', 'backtime', 'backtimes' and 'backtime_positions')


    # splice = [0]
    #
    # for index, storyrow in enumerate(data):
    #     if storyrow["backtime"]:
    #         splice.append(index+1)
    #
    #
    # spliced_data = []
    #
    # for current, next in zip(splice, splice[1:] + [splice[0]]):
    #     spliced_data.append(data[current:next])
    #
    #
    #
    # final_list = []
    #
    # for rd_chunk in spliced_data:

    times = []
    backtime = []
    backtimes = []
    backtime_position = []

    # For loop to increment through each storyrow (previously 'storyline') in the 'data' list
    for storyrow in data:

        if storyrow['backtime'] != "":
            storyrow['totaltime'] = ""


        # Sometimes the TM rundown doesn't have a total-time field, assign a blank one
        if not 'totaltime' in storyrow:
            storyrow['totaltime'] = ""

        # Search the newly created storyrow to see if floated = True or totaltime is empty string
        if storyrow['floated'] == "true" or storyrow['totaltime'] == "":
            # IF so, add NUL value to the 'times' list
            times.append("00:00")
        # Else add the actual totaltime
        else:
            times.append(storyrow['totaltime'])
            #print(storyrow['totaltime'])

        # If backtime is empty, append to backtime_position list
        if storyrow['backtime'] == "":
            # Append empty string
            backtime_position.append("")

        # If backtime is not an empty string, append to backtime list and backtime_position list
        if storyrow['backtime'] != "":
            backtime.append(storyrow["backtime"])
            backtime_position.append(storyrow["backtime"])


            print(datetime.timedelta(seconds=int(storyrow["backtime"][1:])))

    # Two new variables:
    # current_time is retrieved from backtime list (-1 stores last value from list) and strips @ character
    if backtime:
        current_time = int(backtime[-1].strip('@'))
    # get_back_times is currently false and only becomes true when a hard coded backtime is found in the
    # backtime_position list
    get_back_times = False

    # This for loop counts through all of the lists and adds up the backtimes
    for x in range(0, len(times)):
        # The variable this check is a reversed version of backtime_position and is looking at position x in list
        # Checks to see if it is not an empty string
        if list(reversed(backtime_position))[x] != "":
            # And set to True
            get_back_times = True

        # If get_back_times is true, run the if statement
        # if get_back_times == True:
        if get_back_times is True:
            # If '@' is present that indicates a hardcoded backtime
            if "@" in backtime_position[len(backtime_position) - x - 1]:
                # If '@' present current_time will be set to backtime_position
                current_time = int(backtime_position[len(backtime_position) - x - 1].strip('@'))

            # Converting minutes, seconds back to seconds by splitting it up into minutes (m) and seconds (s)
            # and putting it through timedelta(time conversion) and storing it in variable named 'seconds'
            t = (times[len(times) - x - 1])
            m, s = t.split(':')
            current_seconds = (int(datetime.timedelta(minutes=int(m), seconds=int(s)).total_seconds()))

            # current_time will now equal itself minus seconds
            current_time = current_time - int(current_seconds)
            print(str(datetime.timedelta(seconds=current_time)), str(datetime.timedelta(seconds=current_seconds)))
            # Append to backtimes list with current_time converted to hours, minutes, seconds
            backtimes.append(str(datetime.timedelta(seconds=current_time)))
        else:
            # Else append empty string
            backtimes.append("")

    # Flip backtimes list
    backtimes = list(reversed(backtimes))

    # For loop to increment through each storyrow in the 'data' list
    for storyrow in data:

        # Search storyrow to see if floated = False and backtime is empty string
        if storyrow['floated'] != "true" and storyrow['backtime'] == "":
            # If it is the backtime will be set to backtimes at correct position
            storyrow['backtime'] = backtimes[data.index(storyrow)]
        # If '@' is in backtime, strip the @ character and convert to proper time 00:00:00
        if "@" in storyrow["backtime"]:
            storyrow["backtime"] = str(datetime.timedelta(seconds=int(storyrow["backtime"].strip('@'))))





    now = datetime.datetime.now()

    current_hours = now.hour
    current_minutes = now.minute
    current_seconds = now.second

    current_total_seconds = (current_hours * 3600) + (current_minutes * 60) + current_seconds

    # for current_story, next_story in zip(reversed(data), reversed(data[1:] + [data[0]])):
    for current_story in reversed(data):

        if current_story['backtime'] != '' and current_story['backtime'][0] not in ['1', '2']:
            current_story['backtime'] = '0' + current_story['backtime']

        bt_hours = (current_story['backtime'][0:2])
        bt_minutes = (current_story['backtime'][3:5])
        bt_seconds = (current_story['backtime'][6:8])

        if ':' in bt_hours:
            bt_hours = bt_hours[:-1]

        if bt_hours != "":
            story_total_time_seconds = (int(bt_hours) * 3600) + (int(bt_minutes) * 60) + int(bt_seconds)

            if story_total_time_seconds <= current_total_seconds:
                if current_story['totaltime'] != "00:00":
                    current_story['focus'] = 'true'
                    break




    # Open .rundown JSON file located on web server, open in write mode as outfile and dump contents of data to outfile
    with open(filename+'.json', 'w') as outfile:
        outfile.write(json.dumps(data, indent=4, sort_keys=True))


# generate_json("CTS.TX.0600", "0600")
# generate_json("CTS.TX.0630", "0630")
# generate_json("CTS.TX.0700", "0700")
# generate_json("CTS.TX.0800", "0800")
generate_json("CTS.TX.TC3_TM", "test_rundown")
#generate_json("CTS.TX.TC2_LW", "test_rundown")

# generate_json("*GMB-LK.*GMB.TX.0600", "0600")
# generate_json("*GMB-LK.*GMB.TX.0630", "0630")
# generate_json("*GMB-LK.*GMB.TX.0700", "0700")
# generate_json("*GMB-LK.*GMB.TX.0800", "0800")
#generate_json("*GMB-LK.*LK.TX.LORRAINE", "test_rundown")
#generate_json("*TM.*OUTPUT.RUNORDERS.TUESDAY.RUNORDER", "test_rundown")
#generate_json("*LW.RUNORDERS.THURSDAY", "test_rundown")
