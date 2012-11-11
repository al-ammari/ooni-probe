# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

from twisted.python import usage
from twisted.internet import defer

from ooni.utils import log
from ooni.templates import scapyt

from scapy.all import *

class UsageOptions(usage.Options):
    optParameters = [
                    ['backend', 'b', '8.8.8.8', 'Test backend to use'],
                    ['timeout', 't', 5, 'The timeout for the traceroute test'],
                    ['maxttl', 'm', 30, 'The maximum value of ttl to set on packets']
                    ]

class TracerouteTest(scapyt.BaseScapyTest):
    name = "Multi Protocol Traceroute Test"
    author = "Arturo Filastò"
    version = "0.1.1"

    usageOptions = UsageOptions

    dst_ports = [22, 23, 80, 123, 443]
    def max_ttl_and_timeout(self):
        max_ttl = int(self.localOptions['maxttl'])
        timeout = int(self.localOptions['timeout'])
        self.report['max_ttl'] = max_ttl
        self.report['timeout'] = timeout
        return max_ttl, timeout

    def test_tcp_traceroute(self):
        """
        Does a traceroute to the destination by sending TCP SYN packets
        with TTLs from 1 until max_ttl.
        """
        def finished(packets, port):
            log.debug("Finished running TCP traceroute test on port %s" % port)
            answered, unanswered = packets
            self.report['hops_'+str(port)] = [] 
            for snd, rcv in answered:
                report = {'ttl': snd.ttl,
                        'address': rcv.src,
                        'rtt': rcv.time - snd.time 
                }
                log.debug("%s: %s" % (port, report))
                self.report['hops_'+str(port)].append(report)

        dl = []
        max_ttl, timeout = self.max_ttl_and_timeout()
        for port in self.dst_ports:
            packets = IP(dst=self.localOptions['backend'], 
                    ttl=(1,max_ttl),id=RandShort())/TCP(flags=0x2, dport=port)
            d = self.sr(packets, timeout=timeout)
            d.addCallback(finished, port)
            dl.append(d)
        return defer.DeferredList(dl)

    def test_udp_traceroute(self):
        """
        Does a traceroute to the destination by sending UDP packets with empty
        payloads with TTLs from 1 until max_ttl.
        """
        def finished(packets, port):
            log.debug("Finished running UDP traceroute test on port %s" % port)
            answered, unanswered = packets
            self.report['hops_'+str(port)] = []
            for snd, rcv in answered:
                report = {'ttl': snd.ttl,
                        'address': rcv.src,
                        'rtt': rcv.time - snd.time 
                }
                log.debug("%s: %s" % (port, report))
                self.report['hops_'+str(port)].append(report)
        dl = []
        max_ttl, timeout = self.max_ttl_and_timeout()
        for port in self.dst_ports:
            packets = IP(dst=self.localOptions['backend'],
                    ttl=(1,max_ttl),id=RandShort())/UDP(dport=port)
            d = self.sr(packets, timeout=timeout)
            d.addCallback(finished, port)
            dl.append(d)
        return defer.DeferredList(dl)

    def test_icmp_traceroute(self):
        """
        Does a traceroute to the destination by sending ICMP echo request
        packets with TTLs from 1 until max_ttl.
        """
        def finished(packets):
            log.debug("Finished running ICMP traceroute test")
            answered, unanswered = packets
            self.report['hops'] = []
            for snd, rcv in answered:
                report = {'ttl': snd.ttl,
                        'address': rcv.src,
                        'rtt': rcv.time - snd.time 
                }
                log.debug("%s" % (report))
                self.report['hops'].append(report)
        dl = []
        max_ttl, timeout = self.max_ttl_and_timeout()
        packets = IP(dst=self.localOptions['backend'],
                    ttl=(1,max_ttl),id=RandShort())/ICMP()
        d = self.sr(packets, timeout=timeout)
        d.addCallback(finished)
        return d


