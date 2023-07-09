#!/usr/bin/env python3

import pandas as pd
from base64 import urlsafe_b64encode
import time
import os
import sys
import argparse
import configparser
import requests
from time import sleep
from requests.auth import HTTPBasicAuth


sys.path.append(os.path.expanduser('~/.local/lib/python3.11'))
masterdb = "master.csv"

def comp_vendor(kis_read, mac_read):
    vendor_found = pd.DataFrame(columns=['Mac Prefix', 'Vendor Name', 'Private', 'Block Type', 'Last Update'])
    kis_clean2 = kis_read.drop_duplicates()
    for k2tup in kis_clean2.itertuples():
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
    kis_clean1 = kis_read.drop_duplicates()
    for k1tup in kis_clean1.itertuples():
        wig_matches = wig_read.loc[wig_read['MAC'].values == k1tup[1]]
        wigmac_found = pd.concat([wigmac_found, wig_matches])
    return wigmac_found


def check_guests(kis_read, masterdb):
    zero_dict = {'MAC': '00:00:00:00:00:00', 'SSID': '00:00:00:00:00:00',
                 'AuthMode': 'NONE', 'FirstSeen': '0000-00-00 00:00:00',
                 'Channel': '0', 'RSSI': '-00', 'CurrentLatitude': '00.000000',
                 'CurrentLongitude': '-0.000000', 'AltitudeMeters': '0.0',
                 'AccuracyMeters': '0', 'Type': 'WIFI'}
    kis_zero = pd.DataFrame(zero_dict, index=[0])
    if not os.path.exists(masterdb):
        master_df = pd.DataFrame(columns=['MAC', 'SSID', 'AuthMode', 'FirstSeen', 'Channel', 'RSSI',
                                'CurrentLatitude', 'CurrentLongitude', 'AltitudeMeters',
                                'AccuracyMeters', 'Type'])
        master_df = pd.concat([master_df, kis_zero])
        master_df.to_csv(masterdb, sep='\t', encoding='utf-8')
    else:
        master_df = pd.read_csv(masterdb)
    kis_dups = kis_read.drop_duplicates()
    for device in kis_dups.itertuples():
        master_match = master_df.loc[master_df['MAC'].values == device[0]]
        master_df = pd.concat([master_df, master_match])
    return kis_dups


def find_match(kisdb, macdb, wigdb, wigout, vendout, masterdb):
    kis_read = pd.read_csv(kisdb)
    kisc_test = pd.DataFrame(columns=['MAC', 'SSID', 'AuthMode', 'FirstSeen', 'Channel', 'RSSI',
                            'CurrentLatitude', 'CurrentLongitude', 'AltitudeMeters',
                            'AccuracyMeters', 'Type'])
    wig_read = pd.read_csv(wigdb)
    wigc_test = pd.DataFrame(columns=['NAME', 'MAC', 'ENC', 'CHANNEL', 'TIME'])
    kis_test_head = pd.DataFrame(columns=['WigleWifi-1.4'])
    if not wig_read.columns.all == wigc_test.columns.all:
        print('Ooops... Your wigle file is missing its headers... adding them for you...')
        wig_read.columns = ['NAME', 'MAC', 'ENC', 'CHANNEL', 'TIME']
    if kis_read.columns[0] == kis_test_head.columns[0]:
        print('Corrupt Header Present... Cleaning...')
        header_clean(kisdb)
    elif not kis_read.columns.all == kisc_test.columns.all:
        kis_read.columns = ['MAC', 'SSID', 'AuthMode', 'FirstSeen', 'Channel', 'RSSI', 'CurrentLatitude', 'CurrentLongitude', 'AltitudeMeters', 'AccuracyMeters', 'Type']
    kis_new = check_guests(kis_read, masterdb)
    wig_result = comp_kiswigle(kis_new, wig_read)
    mac_read = pd.read_csv(macdb)
    vend_result = comp_vendor(kis_new, mac_read)
    wig_result.to_csv(wigout, sep='\t', encoding='utf-8')
    vend_result.to_csv(vendout, sep='\t', encoding='utf-8')
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
    rdf.to_csv(filename, sep='\t', encoding='utf-8')
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

    prog = os.path.basename(__file__)
    ##################
    # ArgParse Setup #
    ##################
    ap = argparse.ArgumentParser(
        prog=prog,
        usage='%(prog)s.py [-p, (-k, -m, -w)] or [(-c, -a), -f)] or (-d)',
        description='A parser for Kismet to check against Mac and wigle csv'
        'There are three sets of operations.'
        '1. Compare the Kismet csv to both the vendor and wigle csv = (-p)'
        '      This is the main function of this script, and will require you to pass'
        '      the "-p" flag. "-k" and "-w" are mandatory, and if "-m" is excluded,'
        '      it will default to the included mac vendor csv file.'
        '2. Clean a bad header or add a missing header = (-c or -a)'
        '      This set of operations is mostly depracted, and should be performed'
        '      automatically for the user. It exists because the wigle csv file'
        '      includes no heading labels, and the kismet csv included one too many.'
        '3. Download a fresh csv from wigle.net = (-d)'
        '      This provides a convenient means to download a fresh csv file from'
        '      wigle.net. Which if you use this script as intended, will be done'
        '      often. All important configurations for this operation are kept in'
        '      the configuration file.',
        epilog='Remember to convert your kismet DB to CSV',
        conflict_handler='resolve')
    # Arguments for argparse
    ap.add_argument('-p', '--parse', action='store_true',
                    help='Parse the csv files.')
    ap.add_argument('-k', '--kismet',
                    help='Kismet CSV')
    ap.add_argument('-m', '--macdb',
                    help='CSV containing vendor mac addresses')
    ap.add_argument('-w', '--wigle',
                    help='Wigle CSV')
    ap.add_argument('-x', '--wigout',
                    help='Results from wigle')
    ap.add_argument('-z', '--vendout', default='mac-vendors-export.csv',
                    help='Results from vendor')
    ap.add_argument('-c', '--clean', action='store_true',
                    help='Remove first row')
    ap.add_argument('-a', '--add', action='store_true',
                    help='Add missing headers to wigle file')
    ap.add_argument('-f', '--file',
                    help='File for cleaning')
    ap.add_argument('-d', '--download', action='store_true',
                    help='Download wigle db')

    ##################
    # parse the args #
    ##################
    args = ap.parse_args()

    if args.download:
        download_wigle(wigleAPI, wigleToken, lat, lon, dist)
    if args.clean:
        print('This function is mostly deprecated. Ctrl-C to cancel.')
        sleep(5)
        header_clean(args.file)
    if args.add:
        print('This function is mostly deprecated. Ctrl-C to cancel.')
        sleep(5)
        add_headers(args.file)
    if args.parse:
        find_match(args.kismet, args.macdb, args.wigle, args.wigout,
                   args.vendout, masterdb)
        print('Results written to: ' + args.wigout + ' AND ' + args.vendout)


if __name__ == '__main__':
    main()
