# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

from openerp.osv import osv, fields

class res_company(osv.osv):

    _inherit = 'res.company'
    _columns = {
                'rps_sequence_id': fields.many2one('ir.sequence', u'Sequência RPS')
                }

res_company()