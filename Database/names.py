""" Names of values for parsing and saving XMLs.

* Items beginning with NAMES are used as names for saving parsed values.
    Names can be changes, please do not change *_NUM values,
    those are foreign keys.

* Items beginning with LIST are used for parsing XML.
"""

NAMES_POS = ['POSKOZ_D', 'POSKOZ_R', 'DRV_NUM']
NAMES_ZAL = ['ZAL_DR', 'ZAL_DR_P', 'ETZ_NUM']
NAMES_KAT = ['KATEGORIE', 'KAT_SPEC', 'PSK_NUM']
NAMES_DRV = ['DR_ZKR', 'DR_KOD', 'DR_NAZ', 'DR_PUVOD',
             'ZDR_REP', 'ZAST', 'VYSKA', 'TLOUSTKA',
             'BON_R', 'BON_A', 'GEN_KLAS', 'VYB_STR', 'DR_ZAS_TAB',
             'DR_ZAS_HA', 'DR_ZAS_CEL', 'DR_CBP', 'DR_CPP',
             'DR_PMP', 'HMOT', 'HK', 'IMISE', 'DR_KVAL', 'PROC_SOUS',
             'DR_TV', 'DR_TO', 'DR_TVYB', 'ETZ_NUM', 'DRV_NUM']
NAMES_ETZ = ['ETAZ', 'ETAZ_PS', 'ETAZ_PP', 'HS', 'OBMYTI',
             'OBN_DOBA', 'POC_OBNOVY', 'MZD', 'VEK', 'ZAKM', 'HOSP_TV',
             'M_TEZ_PROC', 'ODVOZ_TEZ', 'M_Z_ZASOBY', 'PRO_P', 'PRO_NAL',
             'PRO_POC', 'TV_P', 'TV_NAL', 'TV_POC', 'TO_P', 'TO_NAL',
             'TO_DUVOD', 'TO_ZPUSOB ', 'TVYB_P', 'TVYB_NAL', 'ZAL_DRUH',
             'ZAL_P', 'PSK_NUM', 'ETZ_NUM']
NAMES_VYCH = ['PER', 'VAL', 'ID_ETAZ', 'DREVINA_ZKR', 'TEZBA_CELKEM',
              'VYCHOVA_NAME', 'PSK_NUM']
NAMES_OBN = ['DR', 'INTENZITA', 'ODSTUP', 'TYP', 'PRIRAZENI', 'ZAHAJENI',
             'TEZBA_CELKEM', 'PSK_NUM']

LIST_OBN = ['ID_TAZ_TYP', 'ZAHAJENI', 'TEZBA_CELKEM']
LIST_TAZ = ['ID', 'TYP', 'PRIRAZENI']
LIST_SEC = ['ID', 'ODSTUP']
LIST_ZASAH = ['DR', 'INTENZITA']
LIST_VYCH = ['ID_ETAZ', 'DREVINA_ZKR', 'TEZBA_CELKEM', 'ID_VYCHOVA']
LIST_POS = ['POSKOZ_D', 'POSKOZ_R']
LIST_ZAL = ['ZAL_DR', 'ZAL_DR_P']
LIST_KAT = ['KATEGORIE', 'KAT_SPEC']
LIST_DRV = ['DR_ZKR', 'DR_KOD', 'DR_NAZ', 'DR_PUVOD',
            'ZDR_REP', 'ZAST', 'VYSKA', 'TLOUSTKA',
            'BON_R', 'BON_A', 'GEN_KLAS', 'VYB_STR', 'DR_ZAS_TAB',
            'DR_ZAS_HA', 'DR_ZAS_CEL', 'DR_CBP', 'DR_CPP',
            'DR_PMP', 'HMOT', 'HK', 'IMISE', 'DR_KVAL', 'PROC_SOUS',
            'DR_TV', 'DR_TO', 'DR_TVYB']
LIST_ETZ = ['ETAZ', 'ETAZ_PS', 'ETAZ_PP', 'HS', 'OBMYTI',
            'OBN_DOBA', 'POC_OBNOVY', 'MZD', 'VEK', 'ZAKM', 'HOSP_TV',
            'M_TEZ_PROC', 'ODVOZ_TEZ', 'M_Z_ZASOBY', 'PRO_P', 'PRO_NAL',
            'PRO_POC', 'TV_P', 'TV_NAL', 'TV_POC', 'TO_P', 'TO_NAL',
            'TO_DUVOD', 'TO_ZPUSOB ', 'TVYB_P', 'TVYB_NAL', 'ZAL_DRUH',
            'ZAL_P']
LIST_POR = ['POR', 'SDR_POR', 'MAJ_KOD', 'MAJ_NAZ',
            'MAJ_DRUH', 'ORG_UROVEN', 'PAS_OHR', 'LES_OBL',
            'LES_PODOBL', 'ZVL_STATUT', 'OLH_LIC', 'OLH',
            'POR_TEXT', 'HIST_LHC', 'HIST_LHPOD', 'HIST_ROZD']
LIST_PSK = ['PSK', 'PSK_P0', 'PSK_V', 'PSK_P',
               'KVAL_P', 'ORP', 'KRAJ', 'KATUZE_KOD', 'KAT_PAR_KOD', 'SLT',
               'LT', 'TER_TYP', 'PRIB_VZD', 'HOSP_ZP', 'DAN', 'PSK_TEXT',
               'CISLO_TEL']
LIST_BZL = ['BZL', 'ORP', 'KRAJ', 'KATUZE_KOD', 'BZL_P0',
               'BZL_V', 'BZL_P', 'KVAL_P', 'KAT_PAR_KOD',
               'BZL_VYUZ', 'BZL_DRUH', 'CISLO_TEL']
LIST_JP = ['JP', 'JP_PUPFL', 'ORP', 'KRAJ', 'KATUZE_KOD',
              'JP_P0', 'JP_V', 'JP_P', 'KVAL_P', 'KAT_PAR_KOD',
              'JP_VYUZ', 'JP_DRUH', 'CISLO_TEL']
LIST_KPO = ['PLO_DRUH', 'PLO_ZNACKA', 'PLO_BARVA', 'L_']
LIST_KLO = ['LIN_DRUH', 'LIN_ZNACKA', 'LIN_BARVA', 'L_']
LIST_LHC = ['LHC_KOD', 'LHC_NAZ', 'LHP_OD', 'LHP_DO', 'LHP_LIC',
               'LHP_TAX', 'LHP_Z_OD', 'LHP_Z_DO', 'LHP_Z_LIC', 'LHP_Z_TAX',
               'KU_DATUM', 'LHP_NEZDAR', 'TEZ_PROC', 'NOR_PAS', 'ETAT_TO',
               'LHC_PN_PRO', 'ETAT_TV', 'ETAT_TVYB', 'LHC_IND', 'LHC_MAX',
               'ETAT', 'MVYCH_DO40']
LIST_KBO = ['BOD_DRUH', 'BOD_ZNACKA', 'BOD_UHELZN', 'BOD_BARVA', 'L_']
LIST_KTO = ['TEXT', 'TXT_STYL', 'TXT_UHEL', 'L_']
