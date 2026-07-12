{
    'name': 'EcoSphere ESG Management',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Environmental, Social and Governance Management Platform',
    'description': '''
        EcoSphere ESG Management Platform for Odoo 19 CE.
        Track Environmental (carbon emissions, goals), Social (CSR, challenges),
        and Governance (policies, audits, compliance) with full reporting and gamification.
    ''',
    'author': 'EcoSphere',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'hr',
        'hr_attendance',
        'purchase',
        'stock',
        'fleet',
        'account',
    ],
    'data': [
        # 1. Security first
        'security/esg_security.xml',
        'security/ir.model.access.csv',
        'security/esg_record_rules.xml',
        # 2. Default data
        'data/esg_default_data.xml',
        'data/ir_cron.xml',
        # 3. Views
        'views/department_views.xml',
        'views/category_views.xml',
        'views/emission_factor_views.xml',
        'views/environmental_goal_views.xml',
        'views/policy_views.xml',
        'views/badge_views.xml',
        'views/reward_views.xml',
        'views/carbon_transaction_views.xml',
        'views/csr_activity_views.xml',
        'views/employee_participation_views.xml',
        'views/challenge_views.xml',
        'views/challenge_participation_views.xml',
        'views/policy_acknowledgement_views.xml',
        'views/audit_views.xml',
        'views/compliance_issue_views.xml',
        'views/department_score_views.xml',
        'views/xp_transaction_views.xml',
        'views/res_config_settings_views.xml',
        'views/dashboard_views.xml',
        # 4. Wizards
        'wizards/report_builder_wizard_views.xml',
        # 5. Reports
        'report/esg_report_actions.xml',
        'report/esg_report_templates.xml',
        # 6. Menus (ALWAYS LAST)
        'views/esg_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'esg_management/static/src/scss/esg_dashboard.scss',
            'esg_management/static/src/js/esg_dashboard.js',
            'esg_management/static/src/xml/esg_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
