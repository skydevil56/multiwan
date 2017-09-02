#!/usr/bin/python

import sys
import os
import json

class DefaultParams:
    multiwanconfig="./multiwan.config"
    restore_to_active_high_prio_link = True
    track_ip_addresses = ["8.8.8.8", "8.8.4.4"]
    quantity_of_reachable_ip_addresses = 1
    icmp_interval = 10
    icmp_quantity_to_up_link = 10
    icmp_quantity_to_down_link = 10   
    
class GlobalParams:
    restore_to_active_high_prio_link = None
    track_ip_addresses = []
    quantity_of_reachable_ip_addresses = None
    icmp_interval = None
    icmp_quantity_to_up_link = None
    icmp_quantity_to_down_link = None

class LinkParams:
    def __init__(self):
        self.enabled = None
        self.iface_name = None
        self.description = None 
        self.priority = None
        self.metric = None
        self.next_hop_ip_address = None
        self.track_ip_addresses = []
        self.vrrp_cluster_ip_address = None
        self.restore_to_active_high_prio_link = None
        self.quantity_of_reachable_ip_addresses = None
        self.icmp_interval = None
        self.icmp_quantity_to_up_link = None
        self.icmp_quantity_to_down_link = None
   
def IsGoodIPv4Address(ip):
    try: pieces = ip.split('.')
    except AttributeError: return False
    if len(pieces) != 4: return False
    # FIXME: this func for ip address "0.x.x.x" return True, but it is mistake
    try: return all(0<=int(p)<256 for p in pieces)
    except ValueError: return False
   
def CheckAndParseGlobalParams(multiwanconfig, defaultparams, globalparams):
    with open(multiwanconfig) as json_config:
        try:
            config = json.load(json_config)
        except ValueError:
            print "Incorrect syntax (json) in config file: 'multiwan.config'"
            sys.exit(1)
        else:
            # parse global section
            if "global" in config:
                if "restore_to_active_high_prio_link" in config["global"]:
                    if isinstance(config["global"]["restore_to_active_high_prio_link"], (bool)):
                        globalparams.restore_to_active_high_prio_link = \
                        config["global"]["restore_to_active_high_prio_link"]
                    else:
                        print "Value of 'restore_to_active_high_prio_link' in global section" \
                        " must be bool"
                        sys.exit(1)
                else:
                    globalparams.restore_to_active_high_prio_link = \
                    defaultparams.restore_to_active_high_prio_link

                if "icmp_interval" in config["global"]:
                    if isinstance(config["global"]["icmp_interval"], (int)):
                        globalparams.icmp_interval = \
                        config["global"]["icmp_interval"]
                    else:
                        print "Value of 'icmp_interval' in global section" \
                        " must be integer"
                        sys.exit(1)
                else:
                    globalparams.icmp_interval = \
                    defaultparams.icmp_interval
                
                if "icmp_quantity_to_up_link" in config["global"]:
                    if isinstance(config["global"]["icmp_quantity_to_up_link"], (int)):
                        globalparams.icmp_quantity_to_up_link = \
                        config["global"]["icmp_quantity_to_up_link"]
                    else:
                        print "Value of 'icmp_quantity_to_up_link' in global section" \
                        " must be integer"
                        sys.exit(1)                        
                else:
                    globalparams.icmp_quantity_to_up_link = \
                    defaultparams.icmp_quantity_to_up_link
                
                if "icmp_quantity_to_down_link" in config["global"]:
                    if isinstance(config["global"]["icmp_quantity_to_down_link"], (int)):                
                        globalparams.icmp_quantity_to_down_link = \
                        config["global"]["icmp_quantity_to_down_link"]
                    else:
                        print "Value of 'icmp_quantity_to_down_link' in global section" \
                        " must be integer"
                        sys.exit(1)     
                else:
                    globalparams.icmp_quantity_to_down_link = \
                    defaultparams.icmp_quantity_to_down_link
                    
                if "track_ip_addresses" in config["global"]:
                    if isinstance(config["global"]["track_ip_addresses"], (list)):
                        for ip_address in config["global"]["track_ip_addresses"]:
                            if IsGoodIPv4Address(ip_address):
                                globalparams.track_ip_addresses.append(ip_address)
                            else:
                                print "Format of IP in 'track_ip_addresses' have incorrect value in global config"
                                sys.exit(1)
                    else:
                        print "Incorrect type of 'track_ip_addresses' in global config (must be list)"
                        sys.exit(1)
                else:
                    for ip_address in defaultparams.track_ip_addresses:
                        globalparams.track_ip_addresses.append(ip_address)
                        
                if "quantity_of_reachable_ip_addresses" in config["global"]:
                    if isinstance(config["global"]["quantity_of_reachable_ip_addresses"], (int)):
                        if 1<= config["global"]["quantity_of_reachable_ip_addresses"] <= len(config["global"]["track_ip_addresses"]):
                            globalparams.quantity_of_reachable_ip_addresses = \
                            config["global"]["quantity_of_reachable_ip_addresses"]
                        else:
                            print "Value of 'quantity_of_reachable_ip_addresses' must be >= 1" \
                            " and <= quantity of IPs in 'track_ip_addresses' in global section"
                            sys.exit(1)
                    else:
                        print "Value of 'quantity_of_reachable_ip_addresses' in global section" \
                        " must be integer"
                        sys.exit(1)
                else:
                    globalparams.quantity_of_reachable_ip_addresses = \
                    defaultparams.quantity_of_reachable_ip_addresses
                
            else:
                globalparams.restore_to_active_high_prio_link = \
                defaultparams.restore_to_active_high_prio_link               
                globalparams.quantity_of_reachable_ip_addresses = \
                defaultparams.quantity_of_reachable_ip_addresses                
                globalparams.icmp_interval = \
                defaultparams.icmp_interval
                globalparams.icmp_quantity_to_up_link = \
                defaultparams.icmp_quantity_to_up_link
                globalparams.icmp_quantity_to_down_link = \
                defaultparams.icmp_quantity_to_down_link                    
                for ip_address in defaultparams.track_ip_addresses:
                    globalparams.track_ip_addresses.append(ip_address)                
    
    return True
def CheckLinksParams(multiwanconfig, globalparams):
    iface_names = []
    prioritys = []
    quantity_of_enabled_links = 0
    with open(multiwanconfig) as json_config:
        try:
            config = json.load(json_config)
        except ValueError:
            print "Incorrect syntax (json) in config file: ", multiwanconfig
            sys.exit(1)
        else:
            if "links" in config:
                # check syntax in links section
                if len(config["links"]) == 0:
                    print "Values of 'links' array are empty"
                    sys.exit(1)
                elif len(config["links"]) == 1:
                    print "Multiwan do not support one link, minimum two"
                    sys.exit(1)
                else:
                    for link in config["links"]:
                        if link.get("enabled") is not None and link["enabled"] == True:
                            quantity_of_enabled_links+=1
                            
                            # check iface_name
                            if link.get("iface_name") is not None:
                                if link["iface_name"] in os.listdir("/sys/class/net/"):
                                    if link["iface_name"] not in iface_names: # check unique iface_name in config
                                        iface_names.append(link["iface_name"])
                                    else:
                                        print "Value of 'iface_name' varible in links section must be unique:", \
                                        link["iface_name"], "is present in several links"
                                        sys.exit(1)
                                else:
                                    print "Network interface", link["iface_name"], \
                                    "do not present in system (information based on /sys/class/net/*)"
                                    sys.exit(1)
                            else:
                                print "One link do not have 'iface_name' varible"
                                sys.exit(1)
                            
                            # check next_hop_ip_address
                            if link.get("next_hop_ip_address") is not None:
                                if not IsGoodIPv4Address(link["next_hop_ip_address"]):
                                    print "Link with 'iface_name'", link["iface_name"],  \
                                    "have incorrect format of IP in 'next_hop_ip_address' value"
                                    sys.exit(1)
                            else:
                                print "Link with 'iface_name'", link["iface_name"], \
                                "do not have 'next_hop_ip_address' varible"
                                sys.exit(1)
                                   
                            # check priority
                            if link.get("priority") is not None:
                                if isinstance(link["priority"], (int)) and (1 <= link["priority"] <= 1000) and link["priority"] not in prioritys:
                                    prioritys.append(link["priority"])
                                else:
                                    print "Value of 'priority' varible in links section must be unique " \
                                    "and integer number (range 1 - 1000)"
                                    sys.exit(1)
                            else:
                                print "Link with 'iface_name'", link["iface_name"], \
                                "do not have 'priority' varible"
                                sys.exit(1)
                            
                            # check vrrp_cluster_ip_address
                            if link.get("vrrp_cluster_ip_address") is not None:
                                 if not IsGoodIPv4Address(link["vrrp_cluster_ip_address"]):
                                    print "Link with 'iface_name'", link["iface_name"],  \
                                    "have incorrect format of IP in 'vrrp_cluster_ip_address' value"
                                    sys.exit(1)
                        
                            # check track_ip_addresses and quantity_of_reachable_ip_addresses
                            if link.get("quantity_of_reachable_ip_addresses") is not None and  \
                            link.get("track_ip_addresses") is not None:
                                if isinstance(link["quantity_of_reachable_ip_addresses"], (int)) and \
                                isinstance(link["track_ip_addresses"], (list)) and \
                                (1<= link["quantity_of_reachable_ip_addresses"] <= len(link["track_ip_addresses"])):
                                    for ip_address in link["track_ip_addresses"]:
                                        if not IsGoodIPv4Address(ip_address):
                                            print "Link with 'iface_name'", link["iface_name"],  \
                                            "have incorrect format of IP in 'track_ip_addresses' value"
                                            sys.exit(1)
                                else:
                                    print "Link with 'iface_name'", link["iface_name"],  \
                                    "have incorrect values/types in 'quantity_of_reachable_ip_addresses' (must be integer)" \
                                    "/'track_ip_addresses' (must be list)"
                                    sys.exit(1)
                                
                            elif link.get("quantity_of_reachable_ip_addresses") is not None and \
                            link.get("track_ip_addresses") is None:
                                if not (isinstance(link["quantity_of_reachable_ip_addresses"], (int)) and \
                                isinstance(globalparams.track_ip_addresses, (list)) and \
                                (1<= link["quantity_of_reachable_ip_addresses"] <= len(globalparams.track_ip_addresses))):
                                    print "Link with 'iface_name'", link["iface_name"],  \
                                    "have incorrect values/types in 'quantity_of_reachable_ip_addresses' (must be integer)" \
                                    "/'track_ip_addresses' (must be list, see global section)"
                                    sys.exit(1)
                                    
                            elif link.get("quantity_of_reachable_ip_addresses") is None and \
                            link.get("track_ip_addresses") is not None:
                                if isinstance(globalparams.quantity_of_reachable_ip_addresses, (int)) and \
                                isinstance(link["track_ip_addresses"], (list)) and \
                                (1<= globalparams.quantity_of_reachable_ip_addresses <= len(link["track_ip_addresses"])):
                                    for ip_address in link["track_ip_addresses"]:
                                        if not IsGoodIPv4Address(ip_address):
                                            print "Link with 'iface_name'", link["iface_name"],  \
                                            "have incorrect format of IP in 'track_ip_addresses' value"
                                            sys.exit(1)
                                else:
                                    print "Link with 'iface_name'", link["iface_name"],  \
                                    "have incorrect values/types in 'quantity_of_reachable_ip_addresses' (must be integer, see global section)" \
                                    "/'track_ip_addresses' (must be list)"
                                    sys.exit(1)
                                    
                            elif link.get("quantity_of_reachable_ip_addresses") is None and \
                             link.get("track_ip_addresses") is None:
                                # check in global section
                                pass

                            # check icmp_interval
                            if link.get("icmp_interval") is not None:
                                if not isinstance(link["icmp_interval"], (int)):
                                    print "Link with 'iface_name'", link["iface_name"],  \
                                    "have incorrect type in 'icmp_interval' varible (must be integer)"
                                    sys.exit(1)
                                
                            # check description
                            if link.get("description") is not None:
                                if not isinstance(link["description"], (unicode)):
                                    print "Value of 'description' varible in link section must be a unicode string"
                                    sys.exit(1)
                            
                            # check restore_to_active_high_prio_link
                            if link.get("restore_to_active_high_prio_link") is not None:
                                if not isinstance(link["restore_to_active_high_prio_link"], (bool)):
                                    print "Link with 'iface_name'", link["iface_name"],  \
                                    "have incorrect type in 'restore_to_active_high_prio_link' varible (must be bool)"
                                    sys.exit(1)
                            
                            # check icmp_quantity_to_down_link
                            if link.get("icmp_quantity_to_down_link") is not None:
                                if not isinstance(link["icmp_quantity_to_down_link"], (int)):
                                    print "Link with 'iface_name'", link["iface_name"],  \
                                    "have incorrect type in 'icmp_quantity_to_down_link' varible (must be integer)"
                                    sys.exit(1)
                                    
                            # check icmp_quantity_to_up_link
                            if link.get("icmp_quantity_to_up_link") is not None:
                                if not isinstance(link["icmp_quantity_to_up_link"], (int)):
                                    print "Link with 'iface_name'", link["iface_name"],  \
                                    "have incorrect type in 'icmp_quantity_to_up_link' varible (must be integer)"
                                    sys.exit(1)
                                     
                        else:
                            # multiwan do not pay attention to this links
                            pass
                            
                    # two enabled links are enough that to work properly
                    if quantity_of_enabled_links < 2:
                        print "Multiwan support minimum two enabled link"
                        sys.exit(1)
                     
            else:
                print "Links section is not present in config file:", multiwanconfig
                sys.exit(1)
    
    return True                

def ParseLinksParams(multiwanconfig, globalparams, links):
    with open(multiwanconfig) as json_config:
        try:
            config = json.load(json_config)
        except ValueError:
            print "Incorrect syntax (json) in config file: ", multiwanconfig
            sys.exit(1)
        else:
            for link in config["links"]:
                if link["enabled"] == True:
                    links[link["iface_name"]] = LinkParams() # create dynamic instances of class
                    print links.keys()
                    print len(links[link["iface_name"]].track_ip_addresses)
                    # required parameters
                    links[link["iface_name"]].iface_name = link["iface_name"]
                    links[link["iface_name"]].enabled = link["enabled"]
                    links[link["iface_name"]].priority = link["priority"]
                    links[link["iface_name"]].next_hop_ip_address = link["next_hop_ip_address"]                    
                    print links[link["iface_name"]].iface_name, links[link["iface_name"]].track_ip_addresses
                    
                    
                    # optional parameters
                    if "description" in link:
                        links[link["iface_name"]].description = link["description"]
                    if "vrrp_cluster_ip_address" in link:
                        links[link["iface_name"]].vrrp_cluster_ip_address = link["vrrp_cluster_ip_address"]
                    
                    if "track_ip_addresses" in link:
                        print "if", links[link["iface_name"]].iface_name
                        print links[link["iface_name"]].track_ip_addresses
                        for ip_address in link["track_ip_addresses"]:
                            links[link["iface_name"]].track_ip_addresses.append(ip_address)
                        print links[link["iface_name"]].track_ip_addresses
                        print "--------------------------------"
                    else:
                        print "else", links[link["iface_name"]].iface_name
                        print links[link["iface_name"]].track_ip_addresses
                        for ip_address in globalparams.track_ip_addresses:
                            links[link["iface_name"]].track_ip_addresses.append(ip_address)
                        print  links[link["iface_name"]].track_ip_addresses

    return True
    
def main():
    links = {} # key: iface_name, value: instance of class
    defaultparams = DefaultParams()                
    globalparams = GlobalParams()
    if CheckAndParseGlobalParams(defaultparams.multiwanconfig, defaultparams, globalparams):
        if CheckLinksParams(defaultparams.multiwanconfig, globalparams):
            ParseLinksParams(defaultparams.multiwanconfig, globalparams, links)
            # for key in links.keys():
                # print links[key].iface_name
                # print links[key].enabled
                # print links[key].description
                # print links[key].next_hop_ip_address
                # print links[key].vrrp_cluster_ip_address
                # print links[key].priority
                # print links[key].track_ip_addresses
    
    # print "restore_to_active_high_prio_link", globalparams.restore_to_active_high_prio_link
    # print "quantity_of_reachable_ip_addresses", globalparams.quantity_of_reachable_ip_addresses
    # print "icmp_interval", globalparams.icmp_interval
    # print "icmp_quantity_to_up_link", globalparams.icmp_quantity_to_up_link
    # print "icmp_quantity_to_down_link", globalparams.icmp_quantity_to_down_link
    # print "track_ip_addresses", globalparams.track_ip_addresses

main()    