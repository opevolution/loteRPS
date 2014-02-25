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
import base64
from openerp.osv import fields, osv
from datetime import date
from tools.translate import _
from openerp import netsvc

 
_logger = logging.getLogger(__name__)
 
class cria_rps(osv.osv_memory):
    _name = "cria.rps"
    _description = "Gera RPS a Partir das Faturas"

    _columns = {
                'name': fields.char('nome',size=30,),
                'file': fields.binary('File', readonly=True),
                'filename': fields.char('Filename', size=128),
                'state': fields.selection([('init', 'init'), ('done', 'done')], 'state', readonly=True),
        }

    _defaults = {
        'state': 'init',
        }
     
    def gera_rps(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wf_service = netsvc.LocalService('workflow')     
        [wizard] = self.browse(cr, uid, ids)
        inv_obj = self.pool.get('account.invoice')
        active_ids = context.get('active_ids',[])
          
        obLoterps = self.pool.get('loterps')
         
        _logger.info("Inciando a Geração das RPS")

        result = obLoterps.verifica_rps(cr, uid, active_ids, context)
        
        if not result:
            raise osv.except_osv(_('warning'), _(u'Você selecionou alguma fatura que não esta aberta ou já foi emitida.'))
            return False 

        _logger.info("Inciando a Geração das RPS")

        serie_pool = self.pool.get('l10n_br_account.document.serie')
        [user] = self.pool.get('res.users').browse(cr, uid, [uid])
        [company] = self.pool.get('res.company').browse(cr, user.id, [user.company_id.id])
                
        serie_id = serie_pool.search(cr, uid, [('code','=','NFS'),('company_id','=',user.company_id.id)])[0]
        _logger.info("Series IDS: "+str(serie_id))
        
        if not serie_id:
            raise osv.except_osv(_('warning'), _('Informe uma série para emitir NFS-e, nas configurações da empresa'))
            return False
        else:
            [serie] = serie_pool.browse(cr, uid, [serie_id])
            if not serie.internal_sequence_id:
                raise osv.except_osv(_('warning'), _('Crie uma sequencia para poder exportar RPS.'))
                return False
            else:
                SeqId = serie.internal_sequence_id
        
        _logger.info("Sequencia ID: "+str(SeqId))

        nrLote = obLoterps.gera_id(cr, user.id, company, context)

        rps = obLoterps.gera_rps(cr, uid, active_ids, nrLote, SeqId, context)

        if rps:
         
            LoteRPS = {
                       'name'        : 'RPS_L'+nrLote, 
                       'numero'      : str(nrLote),
                       'data_in'     : date.today(),
                       'data_out'    : date.today(),
                       'company_id'  : company.id,
                       'state'       :'done',
                       }
            
            loterps_id = obLoterps.create(cr, uid, LoteRPS, context)
            #obLoterps.append(loterps_id)
      
            for id in active_ids:
                inv_obj.write(cr, uid, [id], {'loterps_id': loterps_id})
                #wf_service.trg_validate(uid, 'account.invoice', id, 'invoice_open', cr)
            c={}
            #encoded_result = base64.b64encode(rps['arquivo'])

            attach_id=self.pool.get('ir.attachment').create(cr, uid, {
                                        'name': rps['nome'],
                                        'datas': base64.encodestring(rps['arquivo']),
                                        'datas_fname': rps['nome'],
                                        'res_model': 'loterps',
                                        'res_id': loterps_id,
                                        }, context=context)
            
            self.write(cr, uid, [wizard.id], {'filename': rps['nome'],'file': base64.encodestring(rps['arquivo']), 'state': 'done'})
            return True
        else:
            return False
    
cria_rps()   
    
