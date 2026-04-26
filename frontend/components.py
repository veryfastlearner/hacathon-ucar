def create_kpi_card(title: str, value: str):
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """

def alert_card(institution: str, risk_type: str, cause: str, suggested_action: str, level: str):
    css_class = "alert-danger" if level == 'danger' else "alert-warning"
    return f"""
    <div class="alert-card {css_class}">
        <div class="alert-title">{institution} | Flag: {risk_type}</div>
        <div class="alert-text">
            <strong>Diagnostic:</strong> {cause}<br>
            <strong>Recommended Directive:</strong> {suggested_action}
        </div>
    </div>
    """
