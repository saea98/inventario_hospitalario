# Manual migration to create DevolucionProveedor and ItemDevolucion tables

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0025_merge_20251218_1327'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE "inventario_devolucionproveedor" (
                "id" uuid NOT NULL PRIMARY KEY,
                "folio" varchar(50) NOT NULL UNIQUE,
                "estado" varchar(20) NOT NULL,
                "motivo_general" varchar(50) NOT NULL,
                "descripcion" text NULL,
                "contacto_proveedor" varchar(100) NULL,
                "telefono_proveedor" varchar(20) NULL,
                "email_proveedor" varchar(254) NULL,
                "fecha_entrega_estimada" date NULL,
                "numero_autorizacion" varchar(50) NULL UNIQUE,
                "fecha_autorizacion" timestamp with time zone NULL,
                "fecha_entrega_real" date NULL,
                "numero_guia" varchar(100) NULL,
                "empresa_transporte" varchar(100) NULL,
                "numero_nota_credito" varchar(50) NULL UNIQUE,
                "fecha_nota_credito" date NULL,
                "monto_nota_credito" numeric(12, 2) NULL,
                "motivo_cancelacion" text NULL,
                "fecha_creacion" timestamp with time zone NOT NULL,
                "fecha_actualizacion" timestamp with time zone NOT NULL,
                "institucion_id" bigint NOT NULL,
                "proveedor_id" bigint NOT NULL,
                "usuario_autorizo_id" bigint NULL,
                "usuario_creacion_id" bigint NOT NULL
            );

            CREATE TABLE "inventario_itemdevolucion" (
                "id" uuid NOT NULL PRIMARY KEY,
                "cantidad" integer NOT NULL CHECK ("cantidad" >= 0),
                "precio_unitario" numeric(12, 2) NOT NULL,
                "motivo_especifico" text NULL,
                "inspeccionado" boolean NOT NULL,
                "fecha_inspeccion" timestamp with time zone NULL,
                "observaciones_inspeccion" text NULL,
                "fecha_creacion" timestamp with time zone NOT NULL,
                "devolucion_id" uuid NOT NULL,
                "lote_id" bigint NOT NULL,
                "usuario_inspeccion_id" bigint NULL
            );

            ALTER TABLE "inventario_devolucionproveedor" ADD CONSTRAINT "inventario_devolucio_institucion_id_f460d717_fk_inventari" FOREIGN KEY ("institucion_id") REFERENCES "inventario_institucion" ("id") DEFERRABLE INITIALLY DEFERRED;
            ALTER TABLE "inventario_devolucionproveedor" ADD CONSTRAINT "inventario_devolucio_proveedor_id_ffedd666_fk_inventari" FOREIGN KEY ("proveedor_id") REFERENCES "inventario_proveedor" ("id") DEFERRABLE INITIALLY DEFERRED;
            ALTER TABLE "inventario_devolucionproveedor" ADD CONSTRAINT "inventario_devolucio_usuario_autorizo_id_3c49a04b_fk_inventari" FOREIGN KEY ("usuario_autorizo_id") REFERENCES "inventario_user" ("id") DEFERRABLE INITIALLY DEFERRED;
            ALTER TABLE "inventario_devolucionproveedor" ADD CONSTRAINT "inventario_devolucio_usuario_creacion_id_64ee1f3a_fk_inventari" FOREIGN KEY ("usuario_creacion_id") REFERENCES "inventario_user" ("id") DEFERRABLE INITIALLY DEFERRED;

            CREATE INDEX "inventario_devolucionproveedor_folio_9722144d_like" ON "inventario_devolucionproveedor" ("folio" varchar_pattern_ops);
            CREATE INDEX "inventario_devolucionpro_numero_autorizacion_7b143a79_like" ON "inventario_devolucionproveedor" ("numero_autorizacion" varchar_pattern_ops);
            CREATE INDEX "inventario_devolucionpro_numero_nota_credito_b636b66b_like" ON "inventario_devolucionproveedor" ("numero_nota_credito" varchar_pattern_ops);
            CREATE INDEX "inventario_devolucionproveedor_institucion_id_f460d717" ON "inventario_devolucionproveedor" ("institucion_id");
            CREATE INDEX "inventario_devolucionproveedor_proveedor_id_ffedd666" ON "inventario_devolucionproveedor" ("proveedor_id");
            CREATE INDEX "inventario_devolucionproveedor_usuario_autorizo_id_3c49a04b" ON "inventario_devolucionproveedor" ("usuario_autorizo_id");
            CREATE INDEX "inventario_devolucionproveedor_usuario_creacion_id_64ee1f3a" ON "inventario_devolucionproveedor" ("usuario_creacion_id");

            ALTER TABLE "inventario_itemdevolucion" ADD CONSTRAINT "inventario_itemdevol_devolucion_id_1f0de06f_fk_inventari" FOREIGN KEY ("devolucion_id") REFERENCES "inventario_devolucionproveedor" ("id") DEFERRABLE INITIALLY DEFERRED;
            ALTER TABLE "inventario_itemdevolucion" ADD CONSTRAINT "inventario_itemdevol_lote_id_e6d40d04_fk_inventari" FOREIGN KEY ("lote_id") REFERENCES "inventario_lote" ("id") DEFERRABLE INITIALLY DEFERRED;
            ALTER TABLE "inventario_itemdevolucion" ADD CONSTRAINT "inventario_itemdevol_usuario_inspeccion_i_704420e6_fk_inventari" FOREIGN KEY ("usuario_inspeccion_id") REFERENCES "inventario_user" ("id") DEFERRABLE INITIALLY DEFERRED;

            CREATE INDEX "inventario_itemdevolucion_devolucion_id_1f0de06f" ON "inventario_itemdevolucion" ("devolucion_id");
            CREATE INDEX "inventario_itemdevolucion_lote_id_e6d40d04" ON "inventario_itemdevolucion" ("lote_id");
            CREATE INDEX "inventario_itemdevolucion_usuario_inspeccion_id_704420e6" ON "inventario_itemdevolucion" ("usuario_inspeccion_id");
            """,
            reverse_sql="""
            DROP TABLE IF EXISTS "inventario_itemdevolucion" CASCADE;
            DROP TABLE IF EXISTS "inventario_devolucionproveedor" CASCADE;
            """
        ),
    ]
