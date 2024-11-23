## **An Exploratory Data Analysis of U.S Individual Donations for Political Campaigs**


---
A Comissão Federal de Eleições (FEC) é uma agência independente que visa mediar e regular o financiamente de campanhas presidencias dos EUA. Sob o pretexto de registrar cada doação dos cidadãos, criou-se a base que será aqui trabalhada. A partir das bibliotecas **Vega-Altair** e **Plotly**, explora-se a criação de visualizações para compreender e investigar o comportamento das contribuições políticas ao redor do país.


---



### **As variáveis da base**

#### Variáveis Preditivas

* **cmte_id**: ID do comite para o qual a contribuição foi feita. Cada comitê possui um identificador único. Neste dataset estão presentes 7112 comites diferentes.

* **amndt_ind**: Indicador de Emenda. Tal variável é usada para mostrar se uma transação ou um registro é uma emenda a um registro anteriormente apresentado, sendo classificada por uma das três opções:
  * N - Novo registro;

  * A - Emenda a um registro anterior;
  * C - Correção/alteração num registro.

* **rpt_tp**: Tipo de Relatório de contribuição do Comitê ao qual o contribuinte está associado. Seus tipos são comumente diferenciados pela sua recorrência(mensal, trimestral, pré-eleição e etc).

* **transaction_pgi**: Indicador referente a qual etapa do ciclo eleitoral a contribuição em questão está associada.
  *  G - General Election, fase final do ciclo, onde um candidato é eleito para o cargo
  *  P - Primary Election, refere-se às eleições que são internas aos partidos
  *  S - Special Election, eleições convocadas fora do ciclo eleitoral regular para preencher vagas inesperadas
  *  E - Election,
  *  C - Convenction, Convenções Partidárias, que podem ser usadas para selecionar candidatos ou tomar outras decisões internas do partido.
  * O - Other,

  * R - Runoff Election (Segundo Turno)

  * 0 - ??

* **image_num**: Identificador único associado à imagem digitalizada do relatório financeiro.

* **transaction_tp**
  * 10 - Contribuição Financeira direta de um indivíduo ou entidade para um comitê de campanha de um candidato
  * 11 - Contribuição de uma Tribo Nativa
  * 15 - Contribuição financeira direta feita por um indivíduo, sociedade ou LLC (Empresa de responsabilidade limitada) para comitês políticos tradicionais, excluindo Super PACs e Hybrid PACs.
  * 15C - Contribuição de candidatos
  * 15E - Contribuições Direcionadas feitas por indivíduos, sociedades ou LLC para comitês políticos tradicionais
  * 19 - Doação para comunicação eleitoral

  * 20Y - Reembolso de Fundos não Eleitorais. Devolução de fundos que foram originalmente atribuídos a atividades não eleitorais.
  * 21Y - Reembolso de uma Tribo Nativa
  * 22Y - Reembolso de uma contribuição de uma indivíduo, parceiros ou uma empresa de responsabilidade limitada
  * 24I - Contribuição Direcionada por cheque
  * 24T - Contribuição Direcionada utilizando fundos do tesouro do comitê intermediário

* **entity_tp**
  * IND - Individual
  * ORG - Organização
  * CCM - Comitê do Candidato
  * PAC - Comitê de Ação Política
  * CAN - Candidato
  * COM - Comitê

  * PTY - Comitê Oficial do Partido

* **name** - Nome do Contribuinte
* **city** - Cidade do Contribuinte

* **state** - Estado do Contribuinte

* **zip_code** - Código Postal do Contribuinte

* **employer** - Empregador do Contribuinte

* **ocuppation** - Emprego do Contribuinte

* **transaction_dt** - Data de transação das contribuições

* **other_id** - ID de identificação de uma terceira parte envolvida na transação

* **tran_id** - ID único da transação

* **file_num** - Número do arquivo

* **memo_cd** - Identificador associado a presença de um memorando na transação, o qual fornece um contexto adicional à transação

* **memo_text** - Texto do memorando

*  **sub_id** - Identificador de submissão

#### Variável Alvo
* **transaction_amt**: O valor da transação em dólares. Indica a quantidade de dinheiro envolvida em uma contrbuição individual para campanhas políticas.

Assim, o dataset é composto por 5 variáveis de Identificação única, 13 variáveis categóricas, uma variável de texto, uma variável de data e uma varável numérica (alvo)

