define([
    'jquery',
    'knockout',
    'knockout-mapping',
    'views/list',
    'viewmodels/function',
    'bindings/chosen',
    'templates/views/components/functions/generate-unique-references-function.htm'
], function ($, ko, koMapping, ListView, FunctionViewModel, chosen, generateUniqueReferencesFunctionTemplate) {
    const viewModel = function(params) {
        try {
            FunctionViewModel.apply(this, arguments);
            this.nodesSemantic = ko.observableArray();
            this.uniqueresource_nodegroup = params.config.uniqueresource_nodegroup;
            this.triggering_nodegroups = params.config.triggering_nodegroups;
            this.simpleuid_node = params.config.simpleuid_node;
            this.resourceid_node = params.config.resourceid_node;
            this.nodesList = [];

            this.graph.nodes.forEach((node) => {
                if (node.datatype == "semantic" && node.nodegroup_id == node.nodeid) {
                    this.nodesSemantic.push(node);
                } else {
                    this.nodesList.push(node);
                }
            });

            this.graph.nodegroups.forEach((nodegroup) => {
                if (nodegroup.nodegroupid in this.triggering_nodegroups) {
                    // Nodegroup already exists in triggering_nodegroups, do nothing
                } else {
                    this.triggering_nodegroups.push(nodegroup.nodegroupid);
                }
            });

            this.nodesReference = ko.pureComputed(() => {
                const filter = this.uniqueresource_nodegroup();
                if (!filter) return [];
                return this.nodesList.filter(item => item.nodegroup_id === filter);
            });

            this.nodesReferenceNumber = ko.pureComputed(() => {
                return this.nodesReference().filter(node => node.datatype === 'number');
            });

            this.nodesReferenceString = ko.pureComputed(() => {
                return this.nodesReference().filter(node => node.datatype === 'string');
            });

            this.uniqueresource_nodegroup.subscribe((newValue) => {
                console.log('nodesSemantic selection changed:', newValue);
                window.setTimeout(() => { $("select[data-bind^=chosen]").trigger("chosen:updated"); }, 300);
            });            

            window.setTimeout(() => { $("select[data-bind^=chosen]").trigger("chosen:updated"); }, 300);

        }
        catch(err){
            console.error(err.message);
        }
    };

    return ko.components.register('views/components/functions/generate-unique-references-function', {
        viewModel: viewModel,
        template: generateUniqueReferencesFunctionTemplate,
    });
});