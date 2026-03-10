st.subheader("📌 Reservas Especiales del Día")
        
        # Iteramos sobre las filas de reservas (asumiendo que df_res se lee igual que en tu archivo madre)
        for idx, row in df_res.iterrows():
            espacio = str(row[3]).strip() # Columna D: ESPACIO
            
            # Si hay un espacio reservado
            if espacio.lower() not in ["nan", "none", ""]:
                fecha = str(row[0]).strip()  # Columna A: FECHA
                dia = str(row[1]).strip()    # Columna B: DÍA
                bloque = str(row[2]).strip() # Columna C: BLOQUE
                
                # --- LO NUEVO: Leer la Columna F (Avisar al Profesor) ---
                # Usamos el índice 5 (F es la sexta columna)
                aviso_profesor = str(row[5]).strip() if len(row) > 5 else ""
                
                # Filtramos los errores y celdas vacías de Sheets
                if aviso_profesor in ["nan", "#N/A", "#REF!", "", "None"]:
                    texto_extra = ""
                else:
                    # Si hay profesor desplazado, lo agregamos a la derecha
                    texto_extra = f"  {aviso_profesor}"
                
                # Imprimimos la alerta con la info original + el profe desplazado
                st.info(f"⚠️ {espacio} reservado — {dia} {fecha} bloque {bloque}{texto_extra}")
