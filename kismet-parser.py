#!/usr/bin/env python3

import pandas as pd
from base64 import urlsafe_b64encode
import time
import os
import sys
import argparse
import configparser
import requests
from requests.auth import HTTPBasicAuth


sys.path.append(os.path.expanduser('~/.local/lib/python3.11'))
masterdb = "master.csv"

def comp_vendor(kis_read, mac_read):
    vendor_found = pd.DataFrame(columns=['Mac Prefix', 'Vendor Name', 'Private', 'Block Type', 'Last Update'])
    for k2tup in kis_read.itertuples():
        mac_list = str(k2tup[1]).split(':')
        prels = mac_list[:3]
        premac = prels[0] + ':' + prels[1] + ':' + prels[2]
        vend_match = mac_read.loc[mac_read['Mac Prefix'].values == premac]
        ven_strpd = vend_match.drop(columns=['Private', 'Block Type'])
        vend_clean = ven_strpd.drop_duplicates()
        vendor_found = pd.concat([vendor_found, vend_clean])
    return vendor_found


def comp_kiswigle(kis_read, wig_read):
    wigmac_found = pd.DataFrame(columns=['NAME', 'MAC', 'ENC', 'CHANNEL', 'TIME'])
    for k1tup in kis_read.itertuples():
        wig_matches = wig_read.loc[wig_read['MAC'].values == k1tup[0]]
        wigmac_found = pd.concat([wigmac_found, wig_matches])
    return wigmac_found


def add_zero(kis_read):
    zero_list = []
    for x in range(0, len(kis_read.index)):
        x = '0'
        zero_list.append(x)
    return zero_list
    

def convert_dataframe(kis_read, kis_zero):
    zero_list = add_zero(kis_read)
    json_dict = {'MAC': [kis_read['kismet.device.base.macaddr']],
                 'SSID': [kis_read['kismet.device.base.commonname']],
                 'AuthMode': [kis_read['kismet.device.base.crypt']],
                 'FirstSeen': [kis_read['kismet.device.base.first_time']],
                 'Channel': [kis_read['kismet.device.base.channel']],
                 'RSSI': [kis_read['kismet.device.base.name']],
                 'CurrentLatitude': [zero_list],
                 'CurrentLongitude': [zero_list],
                 'AltitudeMeters': [zero_list],
                 'AccuracyMeters': [zero_list],
                 'Type': [zero_list]
                 }
    kis_json = pd.DataFrame(json_dict)
    kis_csv = pd.concat([kis_zero, kis_json])
    return kis_csv


def check_guests(kis_read, masterdb):
    kis_zero = pd.DataFrame(columns=['MAC', 'SSID', 'AuthMode', 'FirstSeen', 'Channel', 'RSSI',
                            'CurrentLatitude', 'CurrentLongitude', 'AltitudeMeters',
                            'AccuracyMeters', 'Type'])
    zero_dict = {'MAC': ['00:00:00:00:00:00'], 'SSID': ['00:00:00:00:00:00'],
                 'AuthMode': ['NONE'], 'FirstSeen': ['0000-00-00 00:00:00'],
                 'Channel': ['0'], 'RSSI': ['0'], 'CurrentLatitude': ['00.000000'],
                 'CurrentLongitude': ['-0.000000'], 'AltitudeMeters': ['0.0'],
                 'AccuracyMeters': ['0'], 'Type': ['WIFI']}
    kis_zero = pd.DataFrame(zero_dict)
    kis_csv = convert_dataframe(kis_read, kis_zero)
    if not os.path.exists(masterdb):
        master_df = pd.DataFrame(columns=['MAC', 'SSID', 'AuthMode', 'FirstSeen', 'Channel', 'RSSI',
                                'CurrentLatitude', 'CurrentLongitude', 'AltitudeMeters',
                                'AccuracyMeters', 'Type'])
        master_df = pd.concat([master_df, kis_csv])
        master_df.to_csv(masterdb, sep=',', encoding='utf-8', index=False)
    else:
        master_df = pd.read_csv(masterdb)
    for device in kis_csv.itertuples():
          master_match = master_df.loc[master_df['MAC'].values == device[0]]
          master_df = pd.concat([master_df, master_match])
    master_df.to_csv(masterdb)
    print('Added entries to master db')
    return kis_read

## -------------------------------------------------------------------------
## for device in kis_dups.itertuples():
##      master_match = master_df.loc[master_df['MAC'].values == device[0]]
##      master_df = pd.concat([master_df, master_match])
## -------------------------------------------------------------------------

def find_match(kisdb, macdb, wigdb, wigout, vendout, masterdb):
    kis_read = pd.read_json(kisdb)
    wig_read = pd.read_csv(wigdb)
    wige_test = pd.DataFrame(columns=['Unnamed: 0', 'NAME', 'MAC', 'ENC', 'CHANNEL', 'TIME'])
    wigc_test = pd.DataFrame(columns=['NAME', 'MAC', 'ENC', 'CHANNEL', 'TIME'])
    if wig_read.columns.all != wige_test.columns.all:
        wig_read = pd.read_csv(wigdb, usecols=['NAME', 'MAC', 'ENC', 'CHANNEL', 'TIME'])
    if wig_read.columns.all != wigc_test.columns.all:
        print('Ooops... Your wigle file is missing its headers... adding them for you...')
        wig_read.columns = ['NAME', 'MAC', 'ENC', 'CHANNEL', 'TIME']
    kis_new = check_guests(kis_read, masterdb)
    wig_result = comp_kiswigle(kis_new, wig_read)
    mac_read = pd.read_csv(macdb)
    vend_result = comp_vendor(kis_new, mac_read)
    wig_result.to_csv(wigout, sep=',', encoding='utf-8', index=False)
    vend_result.to_csv(vendout, sep=',', encoding='utf-8', index=False)
    return True


def download_wigle(wigleAPI, wigleToken, lat, lon, dist):
    rrdf = pd.DataFrame(columns=['NAME', 'MAC', 'ENC', 'CHANNEL', 'TIME'])
    names = []
    macs = []
    encs = []
    chans = []
    times = []
    creds = wigleAPI + wigleToken
    creds_bytes = creds.encode('ascii')
    payload = {'latrange1': lat, 'latrange2': lat, 'longrange1': lon, 'longrange2': lon, 'variance': dist, 'api_key': urlsafe_b64encode(creds_bytes)}
    results = requests.get(url='https://api.wigle.net/api/v2/network/search', params=payload, auth=HTTPBasicAuth(wigleAPI, wigleToken)).json()
    for result in results['results']:
        names.append(result['ssid'])
        macs.append(result['netid'])
        encs.append(result['encryption'])
        chans.append(result['channel'])
        times.append(result['lastupdt'])
    resdict = { 'NAME': names, 'MAC': macs, 'ENC': encs, 'CHANNEL': chans, 'TIME': times }
    redf = pd.DataFrame(resdict)
    rdf = pd.concat([rrdf, redf])
    ftime = time.time()
    time_str = str(ftime).split('.')
    filename = "wigle_results-" + time_str[0] + '.csv'
    rdf.to_csv(filename, sep=',', encoding='utf-8')
    print('Wrote: ' + filename)


def header_clean(file):
    with open(file, 'r', newline='\n') as fin:
        data = fin.read().splitlines(True)
        with open(file, 'w') as fout:
            fout.writelines(data[1:])
            fout.close
    return True


def add_headers(file):
    with open(file, 'r', newline='\n') as rrd:
        data = rrd.read()
        with open(file, 'w') as wrd:
            wrd.write('NAME,MAC,ENC,CHANNEL,TIME')
            wrd.write("\n")
            wrd.writelines(data)
    return True


def main():
    """
    Main
    """
    # Setup config parser
    config = configparser.ConfigParser()
    config_file = "config.ini"
    if not os.path.exists(config_file):
        print('Configuration file is missing')
        exit(1)
    config.read(config_file)
    wigleAPI = config['DEFAULT']['wigle_ID']
    wigleToken = config['DEFAULT']['wigle_Key']
    lat = config['DEFAULT']['lat']
    lon = config['DEFAULT']['long']
    dist = config['DEFAULT']['dist']
    
    vendor_db = os.path.join(os.curdir, 'mac-vendors-export.csv')

    prog = os.path.basename(__file__)
    ##################
    # ArgParse Setup #
    ##################
    ap = argparse.ArgumentParser(
        prog=prog,
        formatter_class=argparse.RawTextHelpFormatter,
        usage='%(prog)s.py [-p, (-k, -m, -w)] or [(-c, -a), -f)] or (-d)',
        description='A parser for Kismet to check against Mac and wigle csv \n'
        '\n'
        'Before you begin: Convert your kismetdb to a json device dump.\n'
        '      "kismetdb_device_dump -i $(YOUR_KISMET_FILE).kismet -o $(OUTPUT_FILE).json"\n'
        '\n'
        'There are two sets of operations.\n'
        '\n'
        '1. Compare the Kismet json to both the vendor and wigle csv = (-p) \n'
        '      This is the main function of this script, and will require you to pass \n'
        '      the "-p" flag. "-k" and "-w" are mandatory, and if "-m" is excluded,\n'
        '      it will default to the included mac vendor csv file.\n'
        '\n'
        '2. Download a fresh csv from wigle.net = (-d)\n'
        '      This provides a convenient means to download a fresh csv file from\n'
        '      wigle.net. Which if you use this script as intended, will be done\n'
        '      often. All important configurations for this operation are kept in\n'
        '      the configuration file.\n'
        '\n'
        'Several applications allow downloading, updating, and maintaining a localized\n'
        'copy of the ieee vendor assigned mac address registry. Which is referred to\n'
        'as the "oui" database. It is reccommended to use these updated databases instead\n'
        'of the one found in this repository. BUT, only if it is in csv format.\n'
        'Both Kismet and Aircrack-NG are two of these applications.\n'
        '\n'
        ,
        epilog='If you find this script useful at all, please be sure to inform me so.\n'
        'As that way I will give a damn about keeping it maintained. Cheers.',
        conflict_handler='resolve')
    # Arguments for argparse
    ap.add_argument('-p', '--parse', action='store_true',
                    help='Parse all the files and search for matching mac addresses.')
    ap.add_argument('-k', '--kismet',
                    help='Kismet Device Json')
    ap.add_argument('-m', '--macdb', default=vendor_db, action='extend',
                    help='CSV containing vendor mac addresses')
    ap.add_argument('-w', '--wigle',
                    help='Wigle CSV')
    ap.add_argument('-x', '--wigout',
                    help='Results from wigle')
    ap.add_argument('-z', '--vendout',
                    help='Results from vendor')
    ap.add_argument('-d', '--download', action='store_true',
                    help='Download wigle db')

    ##################
    # parse the args #
    ##################
    args = ap.parse_args()

    if args.download:
        download_wigle(wigleAPI, wigleToken, lat, lon, dist)
    if args.parse:
        find_match(args.kismet, args.macdb, args.wigle, args.wigout,
                   args.vendout, masterdb)
        print('Results written to: ' + args.wigout + ' AND ' + args.vendout)


if __name__ == '__main__':
    main()
