// product_bundle_all js
odoo.define('product_bundle_all.pos', function(require) {
    "use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');

    var _t = core._t;



    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var product_model = _.find(this.models, function(model){ return model.model === 'product.product'; });
            product_model.fields.push('is_pack','cal_pack_price','pack_ids');            
            return _super_posmodel.initialize.call(this, session, attributes);
        },
    });


    models.load_models({
        model: 'product.pack',
        fields: ['product_id', 'qty_uom', 'bi_product_template', 'bi_image', 'price', 'uom_id', 'name'],
        domain: null,
        loaded: function(self, pos_product_pack) {
            self.pos_product_pack = pos_product_pack;
            self.set({
                'pos_product_pack': pos_product_pack
            });
        },
    });

    models.load_models({
        model: 'product.product',
        fields: ['is_pack','cal_pack_price','pack_ids','name'],
        domain: [['is_pack','=',true]],
        loaded: function(self, pos_product) {
            self.pos_product = pos_product;
            self.set({
                'pos_product': pos_product
            });
        },
    });


    var OrderlineSuper = models.Orderline;
    models.Orderline = models.Orderline.extend({


        get_product_bundle_pack: function() {
            self = this;
            var pos_product_bundle_pack = [];
            var product =  this.get_product();
            var pos_products = self.pos.get('pos_product');
            var pos_product_packs = self.pos.get('pos_product_pack');
            for (var i = 0; i < pos_products.length; i++) {
                if (pos_products[i].id == product.id && (pos_products[i].pack_ids).length > 0) {
                    for (var j = 0; j < (pos_products[i].pack_ids).length; j++) {
                        for (var k = 0; k < pos_product_packs.length; k++) {
                            if (pos_product_packs[k].id == pos_products[i].pack_ids[j]) {
                                var product_items = {
                                    'display_name': pos_product_packs[k].name,
                                    'uom_id': pos_product_packs[k].uom_id,
                                    'price': pos_product_packs[k].price,
                                    'qty_uom': pos_product_packs[k].qty_uom
                                };
                                pos_product_bundle_pack.push({'product': product_items });
                            }
                        }
                    }
                    return pos_product_bundle_pack;
                }
            }
        },
    });
    


});
