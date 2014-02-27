# -*- encoding: utf-8 -*-
################################################################################
#                                                                              #
# Alexandre Defendi - Evoluir Informatica  - Open Evolution                    #
#                                                                              #
# Módulo de Exportação de Lote de RPS                                          #
#                                                                              #
# This program is free software: you can redistribute it and/or modify         #
# it under the terms of the GNU Affero General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or            #
# (at your option) any later version.                                          #
#                                                                              #
# This program is distributed in the hope that it will be useful,              #
# but WITHOUT ANY WARRANTY; without even the implied warranty of               #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
# GNU Affero General Public License for more details.                          #
#                                                                              #
# You should have received a copy of the GNU Affero General Public License     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
#                                                                              #
# versão do módulo : 0.0.1                                                     #
# versao do arquivo: 0.0.1  04/02/2014                                         #
################################################################################

from openerp.osv import orm, fields

class account_invoice(orm.Model):
    _inherit = 'account.invoice'
    _order = "number asc"


    def invoice_confirmada(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'sefaz_export'}, context=context)
        return True

    _columns = {
                'internal_number': fields.char('Invoice Number', size=32, readonly=True, states={'draft':[('readonly',False)]}, help="Unique number of the invoice, computed automatically when the invoice is created."),
                'nro_nfse': fields.integer('Nro. NFS-e'),
                'loterps_id': fields.many2one('loterps', 'Lote RPS',),
               }

account_invoice()