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

import locale
import logging
import base64
import unicodedata
import time
from lxml import etree
from copy import deepcopy
from osv import fields, osv
from openerp import netsvc
from datetime import datetime,date
from openerp.tools.translate import _

CABECALHO_XML = '<?xml version="1.0"?>'

_logger = logging.getLogger(__name__)
Log = True 

def somente_ascii(valor):
    '''
    Usado como decorator para a nota fiscal eletrônica de servicos
    '''
    
    if not isinstance(valor, unicode):
        _logger.info('Não é um unicode!')
        ret = unicodedata.normalize('NFD', unicode(valor)).encode('ascii', 'ignore')
    else:
        ret = unicodedata.normalize('NFD', valor).encode('ascii', 'ignore')
        _logger.info('É um unicode!')
    
    _logger.info("ASCII: "+str(ret))
    return ret

def converte_valor_xml(valor):
    
    ret = '0.00'

    if isinstance(valor, float) or isinstance(valor, int):
        try:
            ret = "%.2f" % valor
        except ValueError:
            pass
    return ret
        
def limpa_cnpj_cpf(cnpj):
    res = cnpj.replace(".","")
    res = res.replace("/","")
    res = res.replace("-","")
    res = res.replace(" ","")
    res = res.replace("(","")
    res = res.replace(")","")
    return res

class loterps(osv.osv):
    """Lote de Recibo Provisório de Serviços"""

    _name = 'loterps'

#     def create_sequence(self, cr, uid, vals, context=None):
#         seq = {
#             'name': vals['name'],
#             'implementation': 'no_gap',
#             'padding': 1,
#             'number_increment': 1}
#         if 'company_id' in vals:
#             seq['company_id'] = vals['company_id']
#         return self.pool.get('ir.sequence').create(cr, uid, seq)


    def gera_id(self, cr, uid, company, context=None):
        if context is None:
            context = {}

        res = False

        if not company.rps_sequence_id:
            raise osv.except_osv(_('warning'), _(u'A RPS deve ter uma sequencia interna')) 
        else:
            _logger.info("Gerar a sequencia ID:"+str(company.rps_sequence_id.id))
            obj_seq = self.pool.get('ir.sequence')
            c = {}
            res = obj_seq.next_by_id(cr, uid, company.rps_sequence_id.id, context=c)
                
        return res    
    
    def anexarRps(self,cr,uid,id,conteudo,nome,context={}):
        if Log:
            _logger.info("Anexando RPS:" + conteudo)
        attach_id=self.pool.get('ir.attachment').create(cr, uid, {
                                                'name': nome,
                                                'datas': base64.encodestring(conteudo),
                                                'datas_fname': nome,
                                                'res_model': 'loterps',
                                                'res_id': id,
                                                }, context=context)
        return True

    def clear_items(self, root):
        for child in root:
            if len(child):
                self.clear_items(child)
            elif not child.text: 
                child.getparent().remove(child)
 
    def gera_arquivo_xml(self, cr, uid, invoice_ids, nrLote, SeqId, context=None):
        """
        Função que gera o arquivo xml para exportar
        @param self: Ponteiro do Objeto
        @param cr: Linha atual do cursor do Banco de Dados,
        @param uid: Usuário atual para controle de acesso,
        @param invoice_ids: Lista dos Invoices contida no lote
        @param context: Um dicionário padrão para valores contextuais
        @return : Arquivo.
        """
        def preenche(tree,context):
            for child in tree:
                tag = child.tag
                valor = context.get(tag)
                if valor is not None:
                    if Log:
                        _logger.info("preenche child: "+str(tag)+" text: "+str(valor))
                    child.text = str(valor)

        if context is None:
            context = {}
         
        var = {}


        if Log:
            _logger.info("locale"+str(locale.getlocale()))
            _logger.info("Numero Lote: "+str(nrLote))
        try:
            nrVlLote = int(nrLote)
        except ValueError:
            nrVlLote = 0   
#         if not isinstance( nrVlLote, ( int, long ) ):
#             if Log:
#                 _logger.info("Numero Lote nao é um inteiro")
#             nrVlLote = 0
    
        [user]    = self.pool.get('res.users').browse(cr, uid, [uid]) 
        empresa   = self.pool.get('res.company').browse(cr, uid, user.company_id.id, context=context)
        mypartner = self.pool.get('res.partner').browse(cr, uid, empresa.partner_id.id, context=context)
        
        MyCidadeCode = mypartner.l10n_br_city_id.state_id.ibge_code+mypartner.l10n_br_city_id.ibge_code
       
        tpFiscal  = self.pool.get('l10n_br_account.partner.fiscal.type').browse(cr, uid, mypartner.partner_fiscal_type_id.id, context=context)
         
        if tpFiscal.code == 'Simples Nacional':
            vlTpFiscal = '1'
        else:
            vlTpFiscal = '2'
         
        if Log:
            _logger.info("Simples Nacional: "+vlTpFiscal)
         
        EnviarLote = etree.XML("<EnviarLoteRpsEnvio></EnviarLoteRpsEnvio>")
        loteRps    = etree.XML("<LoteRps><NumeroLote/><Cnpj/><InscricaoMunicipal/><QuantidadeRps/></LoteRps>")
        ListaRps   = etree.XML("<ListaRps></ListaRps>")
        Rps        = etree.XML("<Rps></Rps>")
        InfRps     = etree.XML("<InfRps><DataEmissao/><NaturezaOperacao/><RegimeEspecialTributacao/><OptanteSimplesNacional/><IncentivadorCultural/><Status/></InfRps>")
        IdentRps   = etree.XML("<IdentificacaoRps><Numero/><Serie/><Tipo/></IdentificacaoRps>")
        Servico    = etree.XML("<Servico><ItemListaServico/><Discriminacao/><CodigoMunicipio/></Servico>")
        ValServ    = etree.XML("<Valores><ValorServicos/><ValorDeducoes/><ValorPis/><ValorCofins/><ValorInss/><ValorIr/><ValorCsll/><IssRetido/><ValorIss/><ValorIssRetido/><Aliquota/><OutrasRetencoes/><BaseCalculo/><ValorLiquidoNfse/><DescontoIncondicionado/><DescontoCondicionado/></Valores>")
        Prestad    = etree.XML("<Prestador><Cnpj/><InscricaoMunicipal/></Prestador>")
        Tomador    = etree.XML("<Tomador><RazaoSocial/></Tomador>")
        ideToma    = etree.XML("<IdentificacaoTomador></IdentificacaoTomador>")
        CNPToma    = etree.XML("<CpfCnpj><Cpf/><Cnpj/></CpfCnpj>")
        EndToma    = etree.XML("<Endereco><Endereco/><Numero/><Complemento/><Bairro/><CodigoMunicipio/><Uf/><Cep/></Endereco>")
        conToma    = etree.XML("<Contato><Telefone/><Email/></Contato>")

         
        loteRps.append( ListaRps )
        EnviarLote.append( loteRps )
        
        if Log:
            _logger.info("1") 
        objInvoice = self.pool.get('account.invoice')
        if Log:
            _logger.info("Invoice IDs:"+str(invoice_ids))
        qtdeRPS = 0
        for invId in invoice_ids:
            qtdeRPS = qtdeRPS + 1     # acumula a quantidade de RPS lido
          
            if Log:
                _logger.info("Invoice ID:"+str(invId))
            invoice = objInvoice.browse(cr, uid, invId, context=context)    # browse  a fatura
            if Log:
                _logger.info(str(invoice.name))
             
            idLine = invoice.invoice_line[0]
            if Log:
                _logger.info("Invoice Line ID: "+str(idLine.id))
            LinhaInv = self.pool.get('account.invoice.line').browse(cr, uid, idLine.id, context=context)  

            ServId = LinhaInv.product_id
            if Log:
                _logger.info("Servico ID: "+str(ServId.id))
            ServInv = self.pool.get('product.product').browse(cr, uid, ServId.id, context=context)
#            if Log:
#                _logger.info("Servico: "+str(ServId.name))
           
            iNatureza = 1
            if invoice.nat_operacao:
                if invoice.nat_operacao == 'no_munic': 
                    iNatureza = 1
                if invoice.nat_operacao == 'fora_munic': 
                    iNatureza = 2
                if invoice.nat_operacao == 'isento': 
                    iNatureza = 3
                if invoice.nat_operacao == 'imune': 
                    iNatureza = 4
                if invoice.nat_operacao == 'susp_judi': 
                    iNatureza = 5
                if invoice.nat_operacao == 'susp_adm': 
                    iNatureza = 6
            _logger.info("Natureza do Serviço: "+str(invoice.nat_operacao)+' ID: '+str(iNatureza))

            iTpServ = self.pool.get('l10n_br_account.service.type').browse(cr, uid, ServInv.service_type_id.id, context=context)
            
            idTipoServico = ''
            if iTpServ:
                idTipoServico = iTpServ.code or ''
                idTipoServico = idTipoServico.replace(".","")
           
            partner  = self.pool.get('res.partner').browse(cr, uid, invoice.partner_id.id, context=context)
            CidadeCode = partner.l10n_br_city_id.state_id.ibge_code+partner.l10n_br_city_id.ibge_code
            
            pFiscal  = self.pool.get('account.fiscal.position').browse(cr, uid, invoice.fiscal_position.id, context=context)
             
            vlServicoPrestado = round(LinhaInv.quantity * LinhaInv.price_unit, 2)
            
            vlDescontos = round(vlServicoPrestado * (LinhaInv.discount/100),2)
            
            vlDeducao = 0
            
            vlBase = vlServicoPrestado - vlDescontos
            
            alISSQN = 0
            vlISSQN = 0
            vlISSQNRet = 0
            vlCSLL = 0
            vlCSLLRet = 0
            vlIR = 0
            vlIRRet = 0
            vlPIS = 0
            vlPISRet = 0
            vlCOFINS = 0
            vlCOFINSRet = 0
            
            _logger.info("Linhas Taxas: "+str(invoice.tax_line))
            
             
            for idLinhaImp in invoice.tax_line:
                [LinhaImp] = self.pool.get('account.invoice.tax').browse(cr, uid, [idLinhaImp.id])
                if vlTpFiscal == '2':
                    _logger.info("Taxa: "+LinhaImp.name+" Valor"+str(LinhaImp.amount))
                    if 'ISSQN' in LinhaImp.name:
                        if LinhaImp.amount > 0:
                            vlISSQN = vlISSQN + LinhaImp.amount
                            alISSQN = round(vlISSQN / vlBase,2) * 100
                        elif LinhaImp.amount < 0:
                            vlISSQNRet = vlISSQNRet + (LinhaImp.amount * (-1))
                    elif 'CSLL' in LinhaImp.name:
                        if LinhaImp.amount > 0:
                            vlCSLL = vlCSLL + LinhaImp.amount
                        elif LinhaImp.amount < 0:
                            vlCSLLRet = vlCSLLRet + (LinhaImp.amount * (-1))
                    elif 'IR' in LinhaImp.name:
                        if LinhaImp.amount > 0:
                            vlIR = vlIR + LinhaImp.amount
                        elif LinhaImp.amount < 0:
                            vlIRRet = vlIRRet + (LinhaImp.amount * (-1))
                    elif 'PIS' in LinhaImp.name:
                        if LinhaImp.amount > 0:
                            vlPIS = vlPIS + LinhaImp.amount
                        elif LinhaImp.amount < 0:
                            vlPISRet = vlPISRet + (LinhaImp.amount * (-1))
                    elif 'COFINS' in LinhaImp.name:
                        if LinhaImp.amount > 0:
                            vlCOFINS = vlCOFINS + LinhaImp.amount
                        elif LinhaImp.amount < 0:
                            vlCOFINSRet = vlCOFINSRet + (LinhaImp.amount * (-1))
            
              
            if Log == True:
                _logger.info("vlServicoPrestado: "+str(vlServicoPrestado))
                _logger.info("vlDescontos: "+str(vlDescontos))
                _logger.info("vlBase: "+str(vlBase))
    
                _logger.info("ISSQN: "+str(vlISSQN))
                _logger.info("ISSQN Ret: "+str(vlISSQNRet))
                _logger.info("CSLL: "+str(vlCSLL))
                _logger.info("CSLL Ret: "+str(vlCSLLRet))
                _logger.info("IR: "+str(vlIR))
                _logger.info("IR Ret: "+str(vlIRRet))
                _logger.info("PIS: "+str(vlPIS))
                _logger.info("PIS Ret: "+str(vlPISRet))
                _logger.info("COFINS: "+str(vlCOFINS))
                _logger.info("COFINS Ret: "+str(vlCOFINSRet))
            
            cpRps      = deepcopy(Rps)
            cpInfRps   = deepcopy(InfRps)
            cpIdentRps = deepcopy(IdentRps)
            cpServico  = deepcopy(Servico)
            cpValServ  = deepcopy(ValServ)
            cpPrestad  = deepcopy(Prestad)
            cpTomador  = deepcopy(Tomador)
            cpEndToma  = deepcopy(EndToma)

            cpIdeToma  = deepcopy(ideToma)
            cpCNPToma  = deepcopy(CNPToma)
            cpEndToma  = deepcopy(EndToma)
            cpConToma  = deepcopy(conToma)
            
            cpInfNFSE = {
                    'DataEmissao'               : date.today().strftime('%Y-%m-%d'),
                    'NaturezaOperacao'          : str(pFiscal.code or ''),
                    'OptanteSimplesNacional'    : vlTpFiscal,
                    'IncentivadorCultural'      : '2',
                    'Status'                    : '1',
                    } 
            preenche(cpInfRps, cpInfNFSE)

            idNFSE = False
            
            if SeqId:
                _logger.info('Seq ID: '+str(SeqId.id))
                if not invoice.nro_nfse:
                    obj_seq = self.pool.get('ir.sequence')
                    c = {}
                    idNFSE = obj_seq.next_by_id(cr, uid, SeqId.id, context=c)
                    objInvoice.write(cr, uid, invoice.id, {'nro_nfse': idNFSE}, context=context)
            
            if idNFSE == False:
                idNFSE = invoice.nro_nfse
            
            cpIdentNFSE = {
                           'Numero': idNFSE,
                           'Serie': '',
                           'Tipo': '1',
                           }

            preenche(cpIdentRps, cpIdentNFSE)
            
            cpServicoNFSE = {
                           'ItemListaServico': idTipoServico,
                           'Discriminacao':  somente_ascii(LinhaInv.name or ServInv.name or ''),
                           'CodigoMunicipio': MyCidadeCode,
                           }

            if not cpServicoNFSE['Discriminacao']:
                raise osv.except_osv(_('warning'), _(u'Discriminação em branco na rps n.'+str(invoice.internal_number)))
                return False
            else:
                if '(copia)' in cpServicoNFSE['Discriminacao']:
                    raise osv.except_osv(_('warning'), _(u'Discriminação contendo "(copia)" na rps n.'+str(invoice.internal_number)))
                    return False

            preenche(cpServico, cpServicoNFSE)

            if vlISSQNRet > 0:
                vlISSQN = vlISSQNRet
                tpISS = 1
                alISSQN = 0
            else:
                alISSQN = 0.05
                tpISS = 2

            TotalRet = vlPISRet+vlCOFINSRet+vlIRRet+vlCSLLRet


# 
#              vlServicoPrestado = round(LinhaInv.quantity * LinhaInv.price_unit, 2)
#             
#             vlDescontos = round(vlServicoPrestado * (LinhaInv.discount/100),2)
#             
#             vlDeducao = 0
#             
#             vlBase = vlServicoPrestado - vlDescontos
           
            cpValServNFSE = {
                           'ValorServicos': converte_valor_xml(vlServicoPrestado),
                           'ValorDeducoes': '0.00',
                           'ValorPis': converte_valor_xml(vlPISRet),
                           'ValorCofins': converte_valor_xml(vlCOFINSRet),
                           'ValorInss': '0.00',
                           'ValorIr': converte_valor_xml(vlIRRet),
                           'ValorCsll': converte_valor_xml(vlCSLLRet),
                           'IssRetido': tpISS, #1 - Retido na Fonte / 2 - Não Retido na Fonte
                           'ValorIss': converte_valor_xml(vlISSQN),
                           'ValorIssRetido': converte_valor_xml(vlISSQNRet),
                           'Aliquota': converte_valor_xml(alISSQN),
                           'OutrasRetencoes': '0.00',
                           'BaseCalculo': converte_valor_xml(vlBase),
                           'ValorLiquidoNfse': converte_valor_xml(vlBase-(TotalRet+vlISSQNRet)),
                           'DescontoIncondicionado': converte_valor_xml(vlDescontos),
                           'DescontoCondicionado': '0.00',
                           }

            preenche(cpValServ, cpValServNFSE)

            cpPrestadNFSE = {
                           'Cnpj': limpa_cnpj_cpf(mypartner.cnpj_cpf or ''),
                           'InscricaoMunicipal': mypartner.inscr_mun or '',
                           }

            preenche(cpPrestad, cpPrestadNFSE)

            cpTomadorNFSE = {
                           'RazaoSocial': somente_ascii(partner.legal_name or ''),
                           }

            preenche(cpTomador, cpTomadorNFSE)

            cpEndTomaNFSE = {
                           'Endereco': somente_ascii(partner.street or ''),
                           'Numero': partner.number or '',
                           'Complemento': somente_ascii(partner.street2 or ''),
                           'Bairro': somente_ascii(partner.district or ''),
                           'CodigoMunicipio': CidadeCode,
                           'Uf': partner.l10n_br_city_id.state_id.code or '',
                           'Cep': str(partner.zip or '').replace("-",""),
                           }

            preenche(cpEndToma, cpEndTomaNFSE)

            if partner.is_company:
                cpCNPTomaNFSE = {
                               'Cnpj': limpa_cnpj_cpf(partner.cnpj_cpf or ''),
                               }
            else:
                cpCNPTomaNFSE = {
                               'Cpf': limpa_cnpj_cpf(partner.cnpj_cpf or ''),
                               }

            preenche(cpCNPToma, cpCNPTomaNFSE)
            #self.clear_items(cpCNPToma)
            
            cpConTomaNFSE = {
                           'Telefone': limpa_cnpj_cpf(partner.phone or ''),
                           'Email': partner.email or '',
                           }

            preenche(cpConToma, cpConTomaNFSE)

            cpIdeToma.append( cpCNPToma )
            cpTomador.append( cpIdeToma )
            cpTomador.append( cpConToma )
            cpTomador.append( cpEndToma )
            cpServico.append( cpValServ )
            cpInfRps.append( cpIdentRps )
            cpInfRps.append( cpServico )
            cpInfRps.append( cpPrestad )
            cpInfRps.append( cpTomador )
            cpRps.append( cpInfRps )
            ListaRps.append( cpRps )
 
        var['NumeroLote'] = str(nrVlLote)
        var['Cnpj'] = limpa_cnpj_cpf(mypartner.cnpj_cpf or '')
        var['InscricaoMunicipal'] = limpa_cnpj_cpf(mypartner.inscr_mun or '') 
        var['QuantidadeRps'] = str(qtdeRPS)
        preenche(loteRps, var)
        self.clear_items(EnviarLote)
 
        
        res = {'arquivo': CABECALHO_XML + etree.tostring(EnviarLote)}
        return res
        
    def gera_rps(self, cr, uid, invoice_ids, nrLote, SeqId=None, context=None):
        if context is None:
            context = {}

        rps = self.gera_arquivo_xml(cr, uid, invoice_ids, nrLote, SeqId, context)
        rps['nome'] ='RPS_L'+nrLote+'_'+time.strftime('%Y%m%d_%H%M%S')+'.xml'
        rps['lote'] ='RPS_L'+nrLote
        return rps
    
    def reemite_rps(self, cr, uid, ids, context=None):
        """Confirma o Processamento do Contrato"""
        if Log:
            _logger.info("Reemite Lote RPS")
        if context is None:
            context = {}
            
        inv_obj = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService('workflow') 
        
        for kid in ids:
            
            rps = self.browse(cr, uid, kid)
            invoice_ids = []
            for invId in  rps.invoice_ids:
                invoice_ids.append(invId.id)
            
            [user] = self.pool.get('res.users').browse(cr, uid, [uid])
            [company] = self.pool.get('res.company').browse(cr, uid, [user.company_id.id])

            nrLote = self.gera_id(cr, uid, company, context)

            LoteRPS = {
                       'name'        : 'RPS_L'+nrLote, 
                       'numero'      : str(nrLote),
                       'data_in'     : date.today(),
                       'data_out'    : date.today(),
                       'company_id'  : company.id,
                       'state'       :'done',
                       }
            
            loterps_id = self.create(cr, uid, LoteRPS, context)

            ArqRps = self.gera_rps(cr, uid, invoice_ids, nrLote, SeqId=None, context=None)

            for nid in invoice_ids:
                inv_obj.write(cr, uid, [nid], {'loterps_id': loterps_id})

            attach_id=self.pool.get('ir.attachment').create(cr, uid, {
                                        'name': ArqRps['nome'],
                                        'datas': base64.encodestring(ArqRps['arquivo']),
                                        'datas_fname': ArqRps['nome'],
                                        'res_model': 'loterps',
                                        'res_id': loterps_id,
                                        }, context=context)
            
            self.write(cr, uid, [kid], {'state': 'cancel'}, context=context)
            
        
        return True

    def regera_rps(self, cr, uid, ids, context=None):
        """Confirma o Processamento do Contrato"""
        if Log:
            _logger.info("contract_confirm")
        if context is None:
            context = {}
        
        for id in ids:
            this = self.browse(cr, uid, id)
            nrLote = this.numero
            invoice_ids = []
            for invId in  this.invoice_ids:
                invoice_ids.append(invId.id)
            rps = self.gera_rps(cr, uid, invoice_ids, nrLote, context=context)
            self.write(cr, uid, ids, {'data_out': time.strftime('%Y-%m-%d')}, context=context)
            self.anexarRps(cr,uid,id,rps['arquivo'],rps['nome'])
        return False

    def emite_rps(self, cr, uid, ids, context=None):
        """Confirma o Processamento do Contrato"""
        serie_pool = self.pool.get('l10n_br_account.document.serie')
        
        _logger.info("contract_confirm")
        if context is None:
            context = {}
        
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
        
        for id in ids:
            this = self.browse(cr, uid, id)
            result = self.verifica_rps(cr, uid, this.invoice_ids, context)
            if result == False:
                return False
        
        for id in ids:
            this = self.browse(cr, uid, id)
            if this.numero:
                nrLote = this.numero
            else:
                nrLote = self.gera_id(cr, uid, company, context)
                self.write(cr, uid, ids, {'name': 'RPS_L'+nrLote, 'numero': str(nrLote)}, context=context)
                
            rps = self.gera_rps(cr, uid, id, nrLote, SeqId, context)
            self.anexarRps(cr,uid,id,rps['arquivo'],rps['nome'])
                
            self.write(cr, uid, [id], {'data_out': time.strftime('%Y-%m-%d'), 'state':'done'}, context=context)
        return True

    def verifica_rps(self, cr, uid, invoice_ids, reemissao=False, context=None):
        msg = False
        [user]    = self.pool.get('res.users').browse(cr, uid, [uid]) 
        empresa   = self.pool.get('res.company').browse(cr, uid, user.company_id.id, context=context) 
        mypartner = self.pool.get('res.partner').browse(cr, uid, empresa.partner_id.id, context=context)       
        for invoice in self.pool.get('account.invoice').browse(cr, uid, invoice_ids):
            if len(invoice.invoice_line) != 1:
                msg = u"A fatura precisa ter 1 item [fatura:"+str(invoice.internal_number)+"]\n"
            else:
                idLine = invoice.invoice_line[0]
                LinhaInv = self.pool.get('account.invoice.line').browse(cr, uid, idLine.id, context=context)  
                ServId = LinhaInv.product_id
                ServInv = self.pool.get('product.product').browse(cr, uid, ServId.id, context=context)
                iTpServ = self.pool.get('l10n_br_account.service.type').browse(cr, uid, ServInv.service_type_id.id, context=context)
                if iTpServ:
                    idTipoServico = iTpServ.code or ''
                    idTipoServico = idTipoServico.replace(".","")
                    if (len(idTipoServico) < 0) or (len(idTipoServico) > 4):
                        msg = u"O serviço precisa ter no seu cadastro a indicação de tipo de serviço. [fatura:"+str(invoice.internal_number)+"]\n"
                else:
                    msg = u"O serviço precisa ter no seu cadastro a indicação de tipo de serviço. [fatura:"+str(invoice.internal_number)+"]\n"

            if (invoice.state != 'sefaz_export') and (not reemissao):
                msg = msg + u"A fatura precisa estar nos estado de envio a Receita [fatura:"+str(invoice.internal_number)+"]\n"
            if invoice.company_id.id != empresa.id:
                msg = msg + u"A empresa na Fatura é diferente da sua empresa.[fatura:"+str(invoice.internal_number)+"]\n"
            if not invoice.partner_id.street:
                msg = msg + u"Informe o endereço do cliente.[fatura:"+str(invoice.internal_number)+"]\n"
            if not invoice.partner_id.cnpj_cpf:
                msg = msg + u"Informe o CNPJ / CPF do cliente.[fatura:"+str(invoice.internal_number)+"]\n"
            if not invoice.partner_id.legal_name:
                msg = msg + u"Informe a Razão Social do cliente.[fatura:"+str(invoice.internal_number)+"]\n"
            if not invoice.partner_id.l10n_br_city_id:
                msg = msg + u"Informe a Cidade do Cliente.[fatura:"+str(invoice.internal_number)+"]\n"
            if not invoice.partner_id.l10n_br_city_id.ibge_code:
                msg = msg + u"Informe o Código IBGE da Cidade do Cliente.[fatura:"+str(invoice.internal_number)+"]\n"
            if not invoice.partner_id.state_id:
                msg = msg + u"Informe a UF do Cliente.[fatura:"+str(invoice.internal_number)+"]\n"
            if not invoice.partner_id.state_id.ibge_code:
                msg = msg + u"Informe o Código IBGE da Cidade do Cliente.[fatura:"+str(invoice.internal_number)+"]\n"
            if not invoice.partner_id.state_id.ibge_code:
                msg = msg + u"Informe o Código IBGE do Estado do Cliente.[fatura:"+str(invoice.internal_number)+"]\n"
            if not mypartner.inscr_mun:
                msg = msg + u"Informe a inscrição municipal da sua empresa\n"
            if not mypartner.cnpj_cpf:
                msg = msg + u"Informe o CNPJ da sua Empresa"
            if not mypartner.l10n_br_city_id.ibge_code:
                msg = msg + u"Informe o Código IBGE da Cidade da Sua Empresa\n"
            if not mypartner.state_id.ibge_code:
                msg = msg + u"Informe o Código IBGE do Estado da Sua Empresa\n"

        return msg 

    _columns = {
                'name': fields.char('Lote', 30, readonly=True),
                'numero': fields.char(u'Número',5),
                'data_in': fields.date(u'Data da Criação',),
                'data_out': fields.date(u'Data de Geração',),
                'invoice_ids' : fields.one2many('account.invoice','loterps_id','Lote RPS', readonly=True),
                'company_id': fields.many2one('res.company', 'Empresa',),
                'state': fields.selection([
                                           ('draft', 'Novo'),
                                           ('done', 'Gerado'),
                                           ('cancel','Cancelado')
                                           ]),
                }
    
    _defaults = {
                'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'ir.attachment', context=c),
                'data_in': lambda *a: time.strftime('%Y-%m-%d'),
                'state': 'draft',
                }

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        #analytic = self.browse(cr, uid, id, context=context)
        default.update(
            name='Teste')
        return super(loterps, self).copy(cr, uid, id, default, context=context)

loterps()
