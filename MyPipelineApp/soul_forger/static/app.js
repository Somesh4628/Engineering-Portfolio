// soul_forger/static/app.js - Fully Upgraded Version

document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Data Store & Element Selectors ---
    const nodes = new vis.DataSet([]);
    const edges = new vis.DataSet([]);
    
    // *** UPDATED: SVG Symbols for Fluidic Components (URL-encoded for better compatibility) ***
    const COMPONENT_ICONS = {
        'Default': 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><circle cx="24" cy="24" r="20" fill="#607d8b" stroke="#37474f" stroke-width="2"/><circle cx="24" cy="24" r="12" fill="#90a4ae"/><text x="24" y="30" text-anchor="middle" fill="white" font-size="18" font-weight="bold">?</text></svg>'),
        'inlet': 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><circle cx="24" cy="24" r="20" fill="#00acc1" stroke="#0097a7" stroke-width="2"/><polygon points="12,18 20,24 12,30" fill="white"/><line x1="28" y1="24" x2="36" y2="24" stroke="white" stroke-width="3" stroke-linecap="round"/></svg>'),
        'outlet': 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><circle cx="24" cy="24" r="20" fill="#d32f2f" stroke="#c62828" stroke-width="2"/><polygon points="36,18 28,24 36,30" fill="white"/><line x1="12" y1="24" x2="20" y2="24" stroke="white" stroke-width="3" stroke-linecap="round"/></svg>'),
        'Tee-Junction': 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><rect x="20" y="8" width="8" height="32" fill="#c0c0be" stroke="#9e9e9e" stroke-width="1"/><rect x="8" y="20" width="32" height="8" fill="#c0c0be" stroke="#9e9e9e" stroke-width="1"/></svg>'),
        'Cross-Junction': 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><rect x="8" y="20" width="32" height="8" fill="#c0c0be" stroke="#9e9e9e" stroke-width="1"/><rect x="20" y="8" width="8" height="32" fill="#c0c0be" stroke="#9e9e9e" stroke-width="1"/></svg>'),
        'Valve': 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><rect x="10" y="18" width="28" height="12" rx="3" fill="#7b1fa2" stroke="#6a1b9a" stroke-width="2"/><circle cx="24" cy="24" r="6" fill="white" stroke="#4a148c" stroke-width="2"/><line x1="18" y1="24" x2="30" y2="24" stroke="#4a148c" stroke-width="2" stroke-linecap="round"/><line x1="24" y1="18" x2="24" y2="30" stroke="#4a148c" stroke-width="2" stroke-linecap="round"/></svg>'),
        'Elbow': 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><path d="M12 36 Q12 12 36 12" stroke="#c0c0be" stroke-width="6" fill="none" stroke-linecap="round"/></svg>'),
        'Tap': 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><circle cx="24" cy="24" r="20" fill="#388e3c" stroke="#2e7d32" stroke-width="2"/><line x1="24" y1="8" x2="24" y2="40" stroke="white" stroke-width="4" stroke-linecap="round"/><line x1="8" y1="24" x2="40" y2="24" stroke="white" stroke-width="4" stroke-linecap="round"/><circle cx="24" cy="24" r="5" fill="white"/></svg>'),
        'Coupling': 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><rect x="8" y="20" width="32" height="8" fill="#c0c0be" stroke="#9e9e9e" stroke-width="1"/><rect x="20" y="16" width="8" height="16" fill="#c0c0be" stroke="#9e9e9e" stroke-width="1"/></svg>')
    };

    const form = document.getElementById('create-form');
    const nodesContainer = document.getElementById('nodes-container');
    const pipesContainer = document.getElementById('pipes-container');
    const actionsContainer = document.getElementById('actions-container');
    const canvas = document.getElementById('network-canvas');
    const loadBlueprintInput = document.getElementById('load_blueprint_file');

    const flawedIds = new Set(JSON.parse(form.dataset.flawedIds || '[]'));

    // --- Preload all component icons to ensure they're available ---
    function preloadIcons() {
        Object.values(COMPONENT_ICONS).forEach(iconUrl => {
            const img = new Image();
            img.src = iconUrl;
        });
    }
    preloadIcons();

    // --- 2. Vis.js Network Initialization ---
    const data = { nodes: nodes, edges: edges };
    const options = {
        interaction: { hover: true, hoverConnectedEdges: true, multiselect: false },
        layout: { improvedLayout: true, randomSeed: 11 },
        physics: {
            enabled: true,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -40,
                centralGravity: 0.015,
                springLength: 160,
                springConstant: 0.03,
                avoidOverlap: 0.4
            },
            stabilization: { iterations: 250, fit: true },
            minVelocity: 0.8
        },
        nodes: {
            shape: 'box',
            borderWidth: 1.4,
            borderWidthSelected: 2.5,
            margin: { top: 12, right: 16, bottom: 12, left: 16 },
            font: {
                size: 14,
                color: '#e2e8f0',
                face: 'Inter',
                align: 'left',
                multi: 'md',
                bold: { face: 'Inter', size: 14, color: '#f8fafc' },
                ital: { face: 'Inter', size: 12, color: '#94a3b8' }
            },
            labelHighlightBold: true,
            shapeProperties: { borderRadius: 10 },
            widthConstraint: { minimum: 180, maximum: 240 },
            heightConstraint: { minimum: 60 },
            color: {
                border: '#334155',
                background: '#1e293b',
                highlight: { border: '#38bdf8', background: '#0f172a' },
                hover: { border: '#38bdf8', background: '#1e293b' }
            },
            shadow: { enabled: true, color: 'rgba(15,23,42,0.45)', size: 18, x: 0, y: 8 }
        },
        edges: {
            width: 2.2,
            smooth: { type: 'continuous', roundness: 0.3 },
            color: { color: '#475569', highlight: '#38bdf8', hover: '#38bdf8' },
            arrows: { to: { enabled: true, scaleFactor: 0.55 } },
            font: { color: '#cbd5f5', size: 11, align: 'middle', face: 'Inter', background: 'rgba(15,23,42,0.55)' },
            shadow: { enabled: true, color: 'rgba(8,15,31,0.4)', size: 8, x: 0, y: 4 }
        }
    };
    const network = new vis.Network(canvas, data, options);

    // --- 3. Counters for Unique IDs ---
    let nodeCounter = 0;
    let pipeCounter = 0;
    let actionCounter = 0;

    // --- Helper Function to Update Component Icon Preview ---
    function updateComponentIcon(selectElement, previewElement) {
        const componentType = selectElement.value;
        let iconSrc = COMPONENT_ICONS.Default; // Default fallback

        // Map component type to icon
        switch (componentType) {
            case 'Tee-Junction':
            case 'Wye-Split':
                iconSrc = COMPONENT_ICONS['Tee-Junction'];
                break;
            case 'Cross-Junction':
                iconSrc = COMPONENT_ICONS['Cross-Junction'];
                break;
            case 'Ball-Valve':
            case 'Gate-Valve':
            case 'Solenoid-Valve':
            case 'Check-Valve':
                iconSrc = COMPONENT_ICONS.Valve;
                break;
            case 'Tap':
                iconSrc = COMPONENT_ICONS.Tap;
                break;
            case '90-Degree-Elbow':
            case '45-Degree-Elbow':
            case 'U-Bend':
                iconSrc = COMPONENT_ICONS.Elbow;
                break;
            case 'Straight-Coupling':
                iconSrc = COMPONENT_ICONS.Coupling;
                break;
            default:
                iconSrc = COMPONENT_ICONS.Default;
        }

        previewElement.style.backgroundImage = `url('${iconSrc}')`;
        previewElement.style.backgroundSize = 'contain';
        previewElement.style.backgroundRepeat = 'no-repeat';
        previewElement.style.backgroundPosition = 'center';
    }

    // --- 4. Core Functions to Add Form Rows (Upgraded for loading data) ---
    function addNodeRow(nodeData = null) {
        nodeCounter++;
        const row = document.createElement('div');
        row.className = 'dynamic-row';
        row.innerHTML = `
            <input type="text" name="node_id_${nodeCounter}" placeholder="Node ID" required>
            <input type="text" name="node_label_${nodeCounter}" placeholder="Display Label">
            <select name="node_type_${nodeCounter}" required>
                <option value="junction">Junction</option><option value="inlet">Inlet</option><option value="outlet">Outlet</option>
            </select>
            <div class="component-selector">
                <select name="component_type_${nodeCounter}" required>
                    <option value="Default">Default</option><option value="Tee-Junction">Tee-Junction</option><option value="90-Degree-Elbow">90° Elbow</option><option value="Tap">Tap</option><option value="Cross-Junction">Cross-Junction</option><option value="Wye-Split">Wye-Split</option><option value="U-Bend">U-Bend</option><option value="Straight-Coupling">Straight-Coupling</option><option value="Ball-Valve">Ball-Valve</option><option value="Gate-Valve">Gate-Valve</option><option value="Check-Valve">Check-Valve</option><option value="Solenoid-Valve">Solenoid-Valve</option>
                </select>
                <div class="component-icon-preview" data-counter="${nodeCounter}"></div>
            </div>
            <div style="display: flex; align-items: center; gap: 5px;">
                <input type="checkbox" name="node_is_critical_${nodeCounter}" value="true" title="Mark as Mission Critical">
                <label style="margin: 0;">Critical</label>
            </div>
            <button type="button" class="delete-btn" title="Delete Row"><i data-lucide="trash-2"></i></button>
        `;
        nodesContainer.appendChild(row);
        lucide.createIcons();

        // Add event listener for component type change
        const componentSelect = row.querySelector(`[name="component_type_${nodeCounter}"]`);
        const iconPreview = row.querySelector('.component-icon-preview');
        componentSelect.addEventListener('change', () => {
            updateComponentIcon(componentSelect, iconPreview);
            updateVisuals(); // Update the visualizer when component type changes
        });
        
        // Also update visuals when node type (role) changes
        const nodeTypeSelect = row.querySelector(`[name="node_type_${nodeCounter}"]`);
        if (nodeTypeSelect) {
            nodeTypeSelect.addEventListener('change', () => updateVisuals());
        }

        if (nodeData) {
            row.querySelector(`[name="node_id_${nodeCounter}"]`).value = nodeData.node_id || `node_${nodeCounter}`;
            row.querySelector(`[name="node_label_${nodeCounter}"]`).value = nodeData.label || '';
            row.querySelector(`[name="node_type_${nodeCounter}"]`).value = nodeData.node_role || 'junction';
            row.querySelector(`[name="component_type_${nodeCounter}"]`).value = nodeData.component_type || 'Default';
            row.querySelector(`[name="node_is_critical_${nodeCounter}"]`).checked = nodeData.is_critical || false;
            updateComponentIcon(componentSelect, iconPreview); // Update icon on load
        } else {
             row.querySelector(`[name="node_id_${nodeCounter}"]`).value = `node_${nodeCounter}`;
             // Initialize with default icon preview
             updateComponentIcon(componentSelect, iconPreview); // Set default icon
        }
        
        // Ensure visuals are updated after a short delay to allow DOM to settle
        setTimeout(() => {
            updateVisuals();
        }, 50);
    }

    function addPipeRow(pipeData = null) {
        pipeCounter++;
        const row = document.createElement('div');
        row.className = 'dynamic-row';
        row.innerHTML = `
            <input type="text" name="pipe_id_${pipeCounter}" placeholder="Pipe ID" required>
            <select name="pipe_source_${pipeCounter}" required></select>
            <select name="pipe_target_${pipeCounter}" required></select>
            <div class="input-group">
                <label for="pipe_length_${pipeCounter}">Length (m)</label>
                <input type="number" id="pipe_length_${pipeCounter}" name="pipe_length_${pipeCounter}" step="0.1" required>
            </div>
            <div class="input-group">
                <label for="pipe_diameter_${pipeCounter}">Diameter (m)</label>
                <input type="number" id="pipe_diameter_${pipeCounter}" name="pipe_diameter_${pipeCounter}" step="0.001" required>
            </div>
            <div class="sensor-config-group">
                <div class="input-group">
                    <label for="pipe_sensor_id_${pipeCounter}">Sensor ID</label>
                    <input type="text" id="pipe_sensor_id_${pipeCounter}" name="pipe_sensor_id_${pipeCounter}" placeholder="Auto-generated">
                </div>
                <div class="input-group">
                    <label for="pipe_gpio_pin_${pipeCounter}">GPIO Pin</label>
                    <input type="number" id="pipe_gpio_pin_${pipeCounter}" name="pipe_gpio_pin_${pipeCounter}" placeholder="Auto" step="1">
                </div>
                <div class="input-group">
                    <label for="pipe_sensor_kfactor_${pipeCounter}">K-Factor (ppl)</label>
                    <input type="number" id="pipe_sensor_kfactor_${pipeCounter}" name="pipe_sensor_kfactor_${pipeCounter}" step="0.1" min="0">
                </div>
            </div>
            <button type="button" class="delete-btn" title="Delete Row"><i data-lucide="trash-2"></i></button>
        `;
        pipesContainer.appendChild(row);
        lucide.createIcons();
        
        if (pipeData) {
            row.querySelector(`[name="pipe_id_${pipeCounter}"]`).value = pipeData.pipe_id || `pipe_${pipeCounter}`;
            row.querySelector(`[name="pipe_length_${pipeCounter}"]`).value = pipeData.properties.length_m || 1.0;
            row.querySelector(`[name="pipe_diameter_${pipeCounter}"]`).value = pipeData.properties.inner_diameter_m || 0.01;
            const sensor = pipeData.flow_sensor || {};
            const sensorIdInput = row.querySelector(`[name="pipe_sensor_id_${pipeCounter}"]`);
            const gpioInput = row.querySelector(`[name="pipe_gpio_pin_${pipeCounter}"]`);
            const kFactorInput = row.querySelector(`[name="pipe_sensor_kfactor_${pipeCounter}"]`);
            if (sensorIdInput) sensorIdInput.value = sensor.sensor_id || '';
            if (gpioInput) gpioInput.value = (sensor.gpio_pin !== undefined && sensor.gpio_pin >= 0) ? sensor.gpio_pin : '';
            if (kFactorInput) kFactorInput.value = sensor.k_factor_ppl || 450.0;
        } else {
            row.querySelector(`[name="pipe_id_${pipeCounter}"]`).value = `pipe_${pipeCounter}`;
            row.querySelector(`[name="pipe_length_${pipeCounter}"]`).value = 1.0;
            row.querySelector(`[name="pipe_diameter_${pipeCounter}"]`).value = 0.01;
            const kFactorInput = row.querySelector(`[name="pipe_sensor_kfactor_${pipeCounter}"]`);
            if (kFactorInput) kFactorInput.value = 450.0;
            const gpioInput = row.querySelector(`[name="pipe_gpio_pin_${pipeCounter}"]`);
            if (gpioInput) gpioInput.value = '';
        }

        const pipeIdInput = row.querySelector(`[name="pipe_id_${pipeCounter}"]`);
        const sensorIdInput = row.querySelector(`[name="pipe_sensor_id_${pipeCounter}"]`);
        const updateSensorPlaceholder = () => {
            if (!sensorIdInput) return;
            const baseId = pipeIdInput && pipeIdInput.value ? pipeIdInput.value : `pipe_${pipeCounter}`;
            const sanitizedId = baseId.replace(/\s+/g, '_');
            sensorIdInput.placeholder = `Auto (S_${sanitizedId})`;
        };
        updateSensorPlaceholder();
        if (pipeIdInput && sensorIdInput) {
            pipeIdInput.addEventListener('input', updateSensorPlaceholder);
        }
    }
    
    function addAiActionRow(actionData = null) {
        actionCounter++;
        const row = document.createElement('div');
        row.className = 'dynamic-row';
        row.innerHTML = `
            <select name="action_fault_class_${actionCounter}" required title="Fault Class"></select>
            <input type="text" name="action_recommendation_${actionCounter}" placeholder="Recommendation" required>
            <select name="action_target_node_${actionCounter}" title="Target Node (Optional)"></select>
            <button type="button" class="delete-btn" title="Delete Action"><i data-lucide="trash-2"></i></button>
        `;
        actionsContainer.appendChild(row);
        lucide.createIcons();
        
        if(actionData){
            row.querySelector(`[name="action_recommendation_${actionCounter}"]`).value = actionData.recommendation || '';
        }
        updateDynamicDropdowns(); 
    }

    // --- 5. Event Listeners ---
    document.getElementById('add-node-btn').addEventListener('click', () => {
        addNodeRow();
        updateVisuals();
    });
    document.getElementById('add-pipe-btn').addEventListener('click', () => {
        addPipeRow();
        updateVisuals();
    });
    document.getElementById('add-action-btn').addEventListener('click', () => addAiActionRow());
    
    loadBlueprintInput.addEventListener('change', handleBlueprintLoad);
    
    form.addEventListener('input', updateVisuals);
    form.addEventListener('change', updateVisuals);

    form.addEventListener('click', (event) => {
        const deleteButton = event.target.closest('.delete-btn');
        if (deleteButton) {
            deleteButton.closest('.dynamic-row').remove();
            updateVisuals();
            updateDynamicDropdowns();
        }
    });

    // --- WORKFLOW UPGRADE: New function to handle loading a blueprint ---
    function handleBlueprintLoad(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                populateFormFromBlueprint(data);
            } catch (error) {
                alert('Error parsing blueprint file: ' + error.message);
            }
        };
        reader.readAsText(file);
        event.target.value = '';
    }
    
    // --- WORKFLOW UPGRADE: New master function to populate the form from data ---
    function populateFormFromBlueprint(data) {
        nodesContainer.innerHTML = '';
        pipesContainer.innerHTML = '';
        actionsContainer.innerHTML = '';
        nodeCounter = 0;
        pipeCounter = 0;
        actionCounter = 0;

        document.getElementById('project_name').value = data.project_details?.name || '';
        if (data.network_info) {
            document.getElementById('network_ssid').value = data.network_info.ssid || '';
            document.getElementById('network_password').value = data.network_info.password || '';
            document.getElementById('telemetry_endpoint').value = data.network_info.telemetry_endpoint || '';
        }
        if (data.ai_model) {
            document.getElementById('ai_model_enabled').checked = data.ai_model.enabled || false;
            document.getElementById('ai_model_filename').value = data.ai_model.model_file || '';
        }
        const availablePinsInput = document.getElementById('available_pins_input');
        if (availablePinsInput) {
            if (Array.isArray(data.available_pins) && data.available_pins.length > 0) {
                availablePinsInput.value = data.available_pins.join(', ');
            } else if (!availablePinsInput.value) {
                availablePinsInput.value = availablePinsInput.getAttribute('value') || '';
            }
        }
        
        data.nodes?.forEach(node => addNodeRow(node));
        data.pipes?.forEach(pipe => addPipeRow(pipe));
        data.ai_model?.prescriptive_actions?.forEach(action => addAiActionRow(action));
        
        updateDynamicDropdowns();
        
        data.pipes?.forEach((pipe, index) => {
            const i = index + 1;
            const sourceSelect = pipesContainer.querySelector(`[name="pipe_source_${i}"]`);
            const targetSelect = pipesContainer.querySelector(`[name="pipe_target_${i}"]`);
            if (sourceSelect) sourceSelect.value = pipe.source_node;
            if (targetSelect) targetSelect.value = pipe.target_node;
        });

        data.ai_model?.prescriptive_actions?.forEach((action, index) => {
             const i = index + 1;
             const targetSelect = actionsContainer.querySelector(`[name="action_target_node_${i}"]`);
             if (targetSelect) targetSelect.value = action.target_node_id || '';
        });

        updateVisuals();
    }

    // --- 6. Core Update and Sync Functions ---
    function updateDynamicDropdowns() {
        const nodeInputs = document.querySelectorAll('input[name^="node_id_"]');
        let nodeOptionsHtml = '<option value="">--Select--</option>';
        nodeInputs.forEach(input => {
            if (input.value.trim() !== '') {
                nodeOptionsHtml += `<option value="${input.value}">${input.value}</option>`;
            }
        });

        const selectors = 'select[name^="pipe_source_"], select[name^="pipe_target_"], select[name^="action_target_node_"]';
        document.querySelectorAll(selectors).forEach(select => {
            const selectedValue = select.value;
            select.innerHTML = nodeOptionsHtml;
            if (Array.from(select.options).some(opt => opt.value === selectedValue)) {
                select.value = selectedValue;
            }
        });
    }

    function updateVisuals() {
        updateDynamicDropdowns();

        const nodeColorPresets = {
            default: {
                border: '#334155',
                background: '#1e293b',
                highlight: { border: '#38bdf8', background: '#0f172a' },
                hover: { border: '#38bdf8', background: '#1e293b' }
            },
            inlet: {
                border: '#0ea5e9',
                background: 'rgba(14, 165, 233, 0.22)',
                highlight: { border: '#38bdf8', background: 'rgba(8, 47, 73, 0.9)' },
                hover: { border: '#38bdf8', background: 'rgba(14, 165, 233, 0.18)' }
            },
            outlet: {
                border: '#f97316',
                background: 'rgba(249, 115, 22, 0.22)',
                highlight: { border: '#fb923c', background: 'rgba(154, 52, 18, 0.85)' },
                hover: { border: '#fb923c', background: 'rgba(249, 115, 22, 0.18)' }
            },
            critical: {
                border: '#f87171',
                background: 'rgba(248, 113, 113, 0.28)',
                highlight: { border: '#ef4444', background: 'rgba(127, 29, 29, 0.9)' },
                hover: { border: '#f87171', background: 'rgba(248, 113, 113, 0.22)' }
            },
            flagged: {
                border: '#facc15',
                background: 'rgba(250, 204, 21, 0.24)',
                highlight: { border: '#fde047', background: 'rgba(113, 63, 18, 0.85)' },
                hover: { border: '#facc15', background: 'rgba(250, 204, 21, 0.2)' }
            }
        };

        const currentNodes = [];
        nodesContainer.querySelectorAll('.dynamic-row').forEach((row) => {
            const idInput = row.querySelector(`input[name^="node_id_"]`);
            const labelInput = row.querySelector(`input[name^="node_label_"]`);
            if (!idInput || !idInput.value) return;

            const id = idInput.value;
            const label = labelInput.value.trim();
            const isCritical = row.querySelector(`input[name^="node_is_critical_"]`).checked;
            
            const nodeRole = row.querySelector(`select[name^="node_type_"]`).value;
            const componentType = row.querySelector(`select[name^="component_type_"]`).value;
            
            // Create a descriptive label that includes component type and node info
            const componentLabel = componentType.replace(/-/g, ' ');
            const roleLabel = nodeRole.replace(/-/g, ' ');
            const displayName = label || id;
            const displayLabel = `**${displayName}**\n${componentLabel}`;

            let nodeObject = { 
                id: id, 
                label: displayLabel,
                title: `${displayName} · ${componentLabel} (${roleLabel})`,
                shape: 'box',
                margin: { top: 12, right: 16, bottom: 12, left: 16 },
                widthConstraint: { minimum: 180, maximum: 240 },
                heightConstraint: { minimum: 60 },
                shapeProperties: { borderRadius: 10 },
                node_role: nodeRole,
                component_type: componentType,
                display_name: displayName,
                component_label: componentLabel,
                isCritical: isCritical,
                isFlagged: flawedIds.has(id)
            };

            // Set colors based on critical status and flaws
            let colorScheme = nodeColorPresets.default;
            if (isCritical) {
                colorScheme = nodeColorPresets.critical;
            } else if (flawedIds.has(id)) {
                colorScheme = nodeColorPresets.flagged;
            } else {
                if (nodeRole === 'inlet') {
                    colorScheme = nodeColorPresets.inlet;
                } else if (nodeRole === 'outlet') {
                    colorScheme = nodeColorPresets.outlet;
                }
            }

            nodeObject.color = colorScheme;
            
            currentNodes.push(nodeObject);
        });

        const currentEdges = [];
        pipesContainer.querySelectorAll('.dynamic-row').forEach((row) => {
            const id = row.querySelector(`input[name^="pipe_id_"]`).value;
            const from = row.querySelector(`select[name^="pipe_source_"]`).value;
            const to = row.querySelector(`select[name^="pipe_target_"]`).value;
            const length = row.querySelector(`input[name^="pipe_length_"]`).value;
            const diameter = row.querySelector(`input[name^="pipe_diameter_"]`).value;
            const sensorId = row.querySelector(`input[name^="pipe_sensor_id_"]`)?.value.trim() || '';
            const gpioPinRaw = row.querySelector(`input[name^="pipe_gpio_pin_"]`)?.value.trim() || '';
            const kFactorRaw = row.querySelector(`input[name^="pipe_sensor_kfactor_"]`)?.value.trim() || '';

            if (id && from && to) {
                const lengthValue = parseFloat(length);
                const diameterValue = parseFloat(diameter);
                const formattedLength = Number.isFinite(lengthValue) ? `${lengthValue.toFixed(lengthValue >= 10 ? 1 : 2)} m` : '';
                const formattedDiameter = Number.isFinite(diameterValue) ? `${(diameterValue * 1000).toFixed(1)} mm` : '';

                const labelParts = [];
                if (formattedLength) labelParts.push(formattedLength);
                if (formattedDiameter) labelParts.push(formattedDiameter);
                if (sensorId) labelParts.push(sensorId);

                const tooltipParts = [
                    `Length: ${formattedLength || 'n/a'}`,
                    `Diameter: ${formattedDiameter || 'n/a'}`,
                    `Sensor: ${sensorId || 'auto-generated'}`,
                    `GPIO Pin: ${gpioPinRaw || 'auto-assigned'}`
                ];
                if (kFactorRaw) {
                    tooltipParts.push(`K-Factor: ${kFactorRaw}`);
                }

                let edgeObject = { 
                    id: id, 
                    from: from, 
                    to: to, 
                    label: labelParts.join('\n'),
                    title: tooltipParts.join('\n')
                };
                if (flawedIds.has(id)) {
                    edgeObject.color = { color: '#facc15', highlight: '#fde047', hover: '#fde047' };
                    edgeObject.width = 4;
                    edgeObject.dashes = [5, 5];
                    edgeObject.font = { color: '#fef08a' };
                }
                currentEdges.push(edgeObject);
            }
        });

        if (currentEdges.length === 0) {
            network.setOptions({ physics: { enabled: false } });
        } else {
            network.setOptions({ physics: { enabled: true } });
        }

        nodes.clear();
        nodes.add(currentNodes);
        edges.clear();
        edges.add(currentEdges);

        network.setData({ nodes, edges });
        
        if (currentNodes.length > 0) {
            network.fit();
        }
    }

    // --- 7. Initial Calls on Page Load ---
    updateDynamicDropdowns();
    updateVisuals();

    // --- 9. Enhanced Interactivity and Animations ---
    // Add staggered animations to dynamic rows
    function animateRows(container, delay = 100) {
        const rows = container.querySelectorAll('.dynamic-row');
        rows.forEach((row, index) => {
            setTimeout(() => {
                row.style.opacity = '0';
                row.style.transform = 'translateY(-20px)';
                row.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                setTimeout(() => {
                    row.style.opacity = '1';
                    row.style.transform = 'translateY(0)';
                }, 50);
            }, index * delay);
        });
    }

    // Animate cards on load
    document.querySelectorAll('.card').forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 200);
    });

    // Enhanced button interactions
    document.addEventListener('click', (event) => {
        const button = event.target.closest('button');
        if (button) {
            button.style.transform = 'scale(0.95)';
            setTimeout(() => {
                button.style.transform = '';
            }, 150);
        }
    });

    // Add glow effect to focused inputs
    document.addEventListener('focusin', (event) => {
        if (event.target.matches('input, select')) {
            event.target.style.boxShadow = '0 0 0 3px rgba(0, 212, 255, 0.3)';
        }
    });

    document.addEventListener('focusout', (event) => {
        if (event.target.matches('input, select')) {
            event.target.style.boxShadow = '';
        }
    });

    // Animate accordion content
    document.addEventListener('change', (event) => {
        if (event.target.classList.contains('accordion-toggle')) {
            const content = event.target.nextElementSibling.nextElementSibling;
            if (event.target.checked) {
                content.style.animation = 'slideInUp 0.4s ease-out';
            }
        }
    });

    let activeTooltip = null;

    function positionTooltip(element, visEvent) {
        const { x, y } = visEvent.pointer.DOM;
        const offset = 18;
        element.style.left = `${x + offset}px`;
        element.style.top = `${y + offset}px`;
    }

    network.on('hoverNode', function(params) {
        const nodeData = nodes.get(params.node);
        if (!nodeData) return;

        if (activeTooltip) {
            activeTooltip.remove();
            activeTooltip = null;
        }

        const tooltip = document.createElement('div');
        tooltip.className = 'network-tooltip visible';
        tooltip.innerHTML = `
            <p class="tooltip-title">${nodeData.display_name || nodeData.id}</p>
            <p class="tooltip-sub">${nodeData.component_label || nodeData.component_type || 'Component'}</p>
            <div class="tooltip-meta">
                <span>${(nodeData.node_role || 'junction').replace(/-/g, ' ')}</span>
                ${nodeData.isCritical ? '<span>critical</span>' : ''}
                ${nodeData.isFlagged ? '<span>flagged</span>' : ''}
            </div>
        `;

        document.body.appendChild(tooltip);
        positionTooltip(tooltip, params.event);
        activeTooltip = tooltip;
    });

    network.on('dragging', function(params) {
        if (activeTooltip && params.event) {
            positionTooltip(activeTooltip, params.event);
        }
    });

    network.on('hoverEdge', function() {
        if (activeTooltip) {
            activeTooltip.classList.remove('visible');
            setTimeout(() => {
                if (activeTooltip) {
                    activeTooltip.remove();
                    activeTooltip = null;
                }
            }, 180);
        }
    });

    network.on('blurNode', function() {
        if (!activeTooltip) return;
        activeTooltip.classList.remove('visible');
        const tooltipToRemove = activeTooltip;
        activeTooltip = null;
        setTimeout(() => {
            if (tooltipToRemove.parentNode) {
                tooltipToRemove.parentNode.removeChild(tooltipToRemove);
            }
        }, 200);
    });

    // Add click animations to nodes
    network.on('click', function(params) {
        if (params.nodes.length === 0) return;
        canvas.classList.add('canvas-flash');
        setTimeout(() => canvas.classList.remove('canvas-flash'), 320);
    });

    // Animate adding new rows
    const originalAddNodeRow = addNodeRow;
    addNodeRow = function(nodeData = null) {
        originalAddNodeRow.call(this, nodeData);
        setTimeout(() => animateRows(nodesContainer), 50);
    };

    const originalAddPipeRow = addPipeRow;
    addPipeRow = function(pipeData = null) {
        originalAddPipeRow.call(this, pipeData);
        setTimeout(() => animateRows(pipesContainer), 50);
    };

    const originalAddAiActionRow = addAiActionRow;
    addAiActionRow = function(actionData = null) {
        originalAddAiActionRow.call(this, actionData);
        setTimeout(() => animateRows(actionsContainer), 50);
    };



    // --- 8. UI ENHANCEMENT: File Input Listeners ---
    function setupFileInputListener(inputId, labelId) {
        const fileInput = document.getElementById(inputId);
        const fileLabel = document.getElementById(labelId);
        if (fileInput && fileLabel) {
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length > 0) {
                    fileLabel.textContent = fileInput.files[0].name;
                } else {
                    fileLabel.textContent = 'Select File...';
                }
            });
        }
    }

    setupFileInputListener('blueprint_file', 'blueprint_file_label_text');
    setupFileInputListener('load_blueprint_file', 'load_blueprint_file_label_text');
    setupFileInputListener('labels_file', 'labels_file_label_text');
});