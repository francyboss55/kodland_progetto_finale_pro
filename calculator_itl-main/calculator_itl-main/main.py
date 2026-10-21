from flask import Flask, render_template, request


app = Flask(__name__)

HOME_MONTHLY_BASE = 100
LIGHT_HOURS = 5
SCREEN_HOURS = 4
OTHER_HOURS = 4

DEVICE_POWER = {
    'computer_hp': 0.3,
    'computer_apple': 0.3,
    'computer_lenovo': 0.3,
    'computer_other': 0.3,
    'tv': 0.1,
    'refrigerator': 1.5,
    'washing_machine': 0.5,
    'dishwasher': 1.2,
    'microwave': 0.2,
    'oven': 2.0,
    'router': 0.1,
    'charger': 0.05,
    'air_conditioner': 1.5,
}

RENEWABLE_GENERATION = {
    'solar': 24,
    'wind': 18,
    'heat_pump': 20,
}

HEATING_CONSUMPTION = {
    'gas': 14,
    'wood': 10,
    'electric': 18,
}

SCREEN_POWER = {
    32: 4,
    55: 7,
    65: 9,
    75: 11,
    85: 14,
}


def number(form, value):
    return max(0, float(form.get(value, 0) or 0))


def computer_brand_total(form):
    return sum(number(form, name) for name in (
        'computer_hp', 'computer_apple', 'computer_lenovo', 'computer_other'
    ))


def calculate_consumption(form):
    size = max(1, int(form.get('size', 1)))
    computers = number(form, 'computers')
    computer_brand_count = computer_brand_total(form)
    if computer_brand_count > 0:
        computers = computer_brand_count
    lights = number(form, 'lights')
    light_hours = number(form, 'light_hours') or LIGHT_HOURS
    screens = number(form, 'screens')
    screen_size = int(form.get('screen_size', 32))
    screen_hours = number(form, 'screen_hours') or SCREEN_HOURS
    other_quantity = number(form, 'other_quantity')
    other_hours = number(form, 'other_hours') or OTHER_HOURS
    other_type = form.get('other_type', 'tv')
    renewable = form.get('renewable') == 'yes'
    renewable_generation = 0
    for renewable_type, count_field in (
        ('solar', 'solar_count'),
        ('wind', 'wind_count'),
        ('heat_pump', 'heat_pump_count'),
    ):
        renewable_generation += number(form, count_field) * RENEWABLE_GENERATION[renewable_type]
    heating = form.get('heating') == 'yes'
    heating_type = form.get('heating_type', 'gas')
    heating_days = number(form, 'heating_days')

    monthly_consumption = size * HOME_MONTHLY_BASE
    monthly_consumption += computers * 0.3 * 30
    monthly_consumption += lights * light_hours * 30 * 0.04
    monthly_consumption += screens * SCREEN_POWER.get(screen_size, 7) * screen_hours * 30
    monthly_consumption += other_quantity * DEVICE_POWER.get(other_type, 0.1) * other_hours * 30
    monthly_consumption += heating_days * HEATING_CONSUMPTION.get(heating_type, 14)

    if not renewable:
        renewable_generation = 0

    net_consumption = max(0, monthly_consumption - renewable_generation)
    renewable_percentage = round((renewable_generation / monthly_consumption * 100), 1) if monthly_consumption else 0
    annual_consumption = round(monthly_consumption * 12, 1)

    return {
        'monthly_consumption': round(monthly_consumption, 1),
        'annual_consumption': annual_consumption,
        'renewable_generation': round(renewable_generation, 1),
        'renewable_percentage': renewable_percentage,
        'net_consumption': round(net_consumption, 1),
    }


def build_recommendations(consumption, renewable_percentage):
    recommendations = []
    if consumption > 3000:
        recommendations.append('Controlla l’uso di climatizzatori, lavatrici e forni: impostare orari e temperature più efficienti riduce molto il consumo.')
    if renewable_percentage < 25:
        recommendations.append('Considera pannelli solari o una turbine eolica per produrre energia propria e ridurre il costo annuale.')
    recommendations.append('Spegni i dispositivi in standby e usa prese intelligenti o timer per evitare consumi invisibili.')
    recommendations.append('Verifica che le lampadine siano LED e sostituisci le più vecchie per ridurre il consumo di illuminazione.')
    return recommendations


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calculator')
def calculator():
    return render_template('calculator.html', form_values={})


@app.route('/calculate', methods=['POST'])
def calculate():
    computers = number(request.form, 'computers')
    computer_brand_count = computer_brand_total(request.form)

    if computers > 0 and computer_brand_count != computers:
        form_values = request.form.to_dict()
        form_values['computers'] = '0'
        return render_template(
            'calculator.html',
            form_values=form_values,
            error_message=(
                'Il numero di computer deve essere uguale alla somma delle '
                'quantità per marca. Controlla i valori e riprova.'
            ),
        )

    consumption = calculate_consumption(request.form)
    renewable_percentage = consumption['renewable_percentage']

    if renewable_percentage >= 50 and consumption['monthly_consumption'] <= 2500:
        status_title = 'La casa è molto efficiente!'
        status_message = 'Il tuo sistema produce una parte importante dell’energia necessaria. Continua così e verifica ogni anno il rendimento degli impianti.'
        status_class = 'status-card--good'
    elif renewable_percentage >= 25:
        status_title = 'La casa è abbastanza efficiente!'
        status_message = 'La produzione rinnovabile copre una parte consistente del consumo. Migliora comunque le abitudini per aumentare il risparmio.'
        status_class = 'status-card--good'
    else:
        status_title = 'La casa ha bisogno di miglioramenti'
        status_message = 'Il consumo è alto rispetto alla produzione rinnovabile. Alcune modifiche semplici possono aiutare a ridurlo.'
        status_class = 'status-card--bad'

    return render_template(
        'result.html',
        **consumption,
        status_title=status_title,
        status_message=status_message,
        status_class=status_class,
        recommendations=build_recommendations(
            consumption['monthly_consumption'], renewable_percentage
        ),
    )


if __name__ == '__main__':
    app.run(debug=True)
