function featuresMixin() {
    return {
        featureSaving: false,

        featureLabel(name) {
            const labels = {
                flight_tracking: 'Flight Tracking',
                oil_consumption: 'Oil Consumption',
                fuel_consumption: 'Fuel Consumption',
                oil_analysis: 'Oil Analysis',
                airworthiness_enforcement: 'Airworthiness Enforcement',
                sharing: 'Public Sharing',
            };
            return labels[name] || name;
        },

        featureDescription(name) {
            const descriptions = {
                flight_tracking: 'Flight log tab and Log Flight button',
                oil_consumption: 'Oil usage records and consumption chart',
                fuel_consumption: 'Fuel usage records and burn rate chart',
                oil_analysis: 'Oil analysis lab report tracking',
                airworthiness_enforcement: 'Block flight logging and hour updates when aircraft is grounded',
                sharing: 'Share links and public access',
            };
            return descriptions[name] || '';
        },

        async toggleFeature(featureName, enabled) {
            this.featureSaving = true;
            try {
                const { ok, data } = await apiRequest(
                    `/api/aircraft/${this.aircraftId}/features/`,
                    {
                        method: 'POST',
                        body: JSON.stringify({ feature: featureName, enabled }),
                    }
                );
                if (!ok) throw data;
                this.features = data.features;

                showNotification(
                    `Feature "${this.featureLabel(featureName)}" ${enabled ? 'enabled' : 'disabled'}`,
                    'success'
                );
            } catch (err) {
                showNotification('Failed to update feature: ' + formatApiError(err), 'danger');
            } finally {
                this.featureSaving = false;
            }
        },
    };
}
