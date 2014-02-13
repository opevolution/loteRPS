# -*- coding: utf-8 -*-
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

import logging
from openerp.osv import fields, osv
from datetime import date
 
_logger = logging.getLogger(__name__)
 
class cria_rps(osv.osv_memory):
    _name = "cria.rps"
    _description = "Gera RPS a Partir das Faturas"

    _columns = {
                'name': fields.char('nome',size=30,),
                'state': fields.selection([('init', 'init'),
                                           ('done', 'done')], 'state', readonly=True),
        }

    _defaults = {
        'state': 'init',
        }
     
    def gera_rps(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
             
        obLoterps = self.pool.get('loterps')
         
        _logger.info("Inciando a Geração das RPS")
  
        LoteRPS = {
                   'data_in'     : date.today(),
                   }
 
        loterps_id = obLoterps.create(cr, uid, LoteRPS, context)
        #obLoterps.append(loterps_id)
 
  
        inv_obj = self.pool.get('account.invoice')
        active_ids = context.get('active_ids',[])
          
        for id in active_ids:
            inv_obj.write(cr, uid, [id], {'loterps_id': loterps_id})

cria_rps()   
    
