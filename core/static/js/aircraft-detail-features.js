function featuresMixin() {
    return {
        featureSaving: false,

        featureLabel(name) {
            const entry = this.featureCatalog.find(f => f.name === name);
            return entry ? entry.label : name;
        },

        featureDescription(name) {
            const entry = this.featureCatalog.find(f => f.name === name);
            return entry ? entry.description : '';
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
                if (data.feature_catalog) this.featureCatalog = data.feature_catalog;

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
