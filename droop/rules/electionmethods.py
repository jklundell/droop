'''
election rule methods helpers

Copyright 2010 by Jonathan Lundell

This file is part of Droop.

    Droop is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Droop is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Droop.  If not, see <http://www.gnu.org/licenses/>.
'''

from __future__ import absolute_import
from .electionrule import ElectionRule

# pylint: disable=W0223,E1101

class MethodMeek(ElectionRule):
    '''
    MethodMeek is a convenience class for Meek-based rules.
    It supplies generic Meek record handlers.
    
    A rule can subclass MethodMeek instead of ElectionRule to use these handlers.
    '''
    method = "meek"

    def action(self, record, action=None):
        '''
        meek-specific election action recording.
        See record.ElectionRecord.action() for details.
        '''
        if action is None:
            record['omega'] = self.omega
        else:
            action['residual'] = self.E.residual  # meek residual is the nontransferable portion
            action['surplus'] = self.E.surplus

    def report(self, record, report, section, action=None):
        '''
        meek-specific election reporting.
        See record.ElectionRecord.report() for details.
        '''
        if section == 'headerappend':
            report.append("\tOmega: %s\n" % record.get('omega'))
        elif section == 'actionappend':
            s =  '\tQuota: %s\n' % action['quota']
            s += '\tVotes: %s\n' % action['votes']
            s += '\tResidual: %s\n' % action['residual']
            s += '\tTotal: %s\n' % (action['votes'] + action['residual'])
            s += '\tSurplus: %s\n' % action['surplus']
            report.append(s)
        else:
            return False
        return True

    def dump(self, line, action=None, cid=None, cstate=None):
        "append meek-specific dump info"
        if cid is None:
            if action is None:  # header
                line += ['Votes', 'Surplus', 'Residual']
            else:
                line += [action['votes'], action['surplus'], action['residual']]
        else:
            if action is None:  # header
                line += ['%s.vote' % cid, '%s.kf' % cid]
            else:
                line += [cstate['vote'], cstate['kf']]

class MethodWIGM(ElectionRule):
    '''
    MethodWIGM is a convenience class for WIGM-based rules.
    It supplies generic WIGM record handlers.
    
    A rule can subclass MethodWIGM instead of ElectionRule to use these handlers.
    '''
    method = "wigm"

    def action(self, record, action=None):
        '''
        wigm-specific election action recording.
        See record.ElectionRecord.action() for details.
        '''
        if action is not None:
            action['nt_votes'] = self.E.exhausted # nontransferable votes
            action['surplus'] = self.E.surplus

    def report(self, record, report, section, action=None):
        '''
        wigm-specific election reporting.
        See record.ElectionRecord.report() for details.
        '''
        if section == 'actionappend':
            E = self.E
            cids = record['cids']
            cstate = action['cstate']
            ecids = [cid for cid in cids if cstate[cid]['state'] == 'elected']
            hcids = [cid for cid in cids if cstate[cid]['state'] == 'hopeful']
            dcids = [cid for cid in cids if cstate[cid]['state'] == 'defeated']
            h_votes = sum([cstate[cid]['vote'] for cid in hcids], E.V0)
            d_votes = sum([cstate[cid]['vote'] for cid in dcids], E.V0)
            e_votes = sum([cstate[cid]['vote'] for cid in ecids if not cstate[cid]['pending']], E.V0)
            p_votes = sum([cstate[cid]['vote'] for cid in ecids if cstate[cid]['pending']], E.V0)
            total = e_votes + p_votes + h_votes + d_votes + action['nt_votes']  # vote total
            residual = E.V(record['nballots']) - total          # votes lost due to rounding error
            s =  '\tElected votes: %s\n' % e_votes
            if p_votes:
                s += '\tPending votes: %s\n' % p_votes
            s += '\tHopeful votes: %s\n' % h_votes
            if d_votes:
                s += '\tDefeated votes: %s\n' % d_votes
            s += '\tNontransferable votes: %s\n' % action['nt_votes']
            s += '\tResidual: %s\n' % residual
            s += '\tTotal: %s\n' % (total + residual)
            s += '\tSurplus: %s\n' % action['surplus']
            report.append(s)
        else:
            return False
        return True

    def dump(self, line, action=None, cid=None, cstate=None):
        "append wigm-specific dump info"
        if cid is None:
            if action is None:  # header
                line += ['Non-Transferable']
            else:
                line += [action['nt_votes']]
        else:
            if action is None:  # header
                line += ['%s.vote' % cid]
            else:
                line += [cstate['vote']]
