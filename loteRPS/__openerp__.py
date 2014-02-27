# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014  Alexandre Defendi - Open Evolution - Brazil             #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
#                                                                             #
# -versao_modulo  0.0        elvio.desenvolvimento@gmail.com                  #
# -versao_arquivo 0.1                                                         #
###############################################################################
{   
    'name'          : 'Emissão de Lote de R.P.S. para a prefeitura de Curitiba/PR',
    'version'       : '0.007',
    'author'        : 'Alexandre Defendi @ Open Evoluir',
    'website'       : 'www.evoluirinformatica.com.br',
    'category'      : 'Account',
    'description'   : '''
Emissão de Lote para importação de RPS na NFS-e da prefeitura de Curitiba
=========================================================================
02/02/2014            Alexandre Defendi  Versão Inicial do Projeto ''',
    'depends'       : ['l10n_br_account',],
    'init_xml'      : [],
    'update_xml'    : ['root_menus.xml',
                       'loterps_view.xml',
                       'res_company_view.xml',
                       'account_invoice_view.xml',
                       'wizard/cria_rps_view.xml',
                       'partner_view.xml',
                       ],
    'demo_xml'      : [],
    'active'        : False,
    'installable'   : True,
}
