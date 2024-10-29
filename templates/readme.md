Máscara para número da OAB e número do processo em javascript puro:

    const numeroProcessoInput = document.getElementById('numero_processo');
    const numeroOabInput = document.getElementById('numero_oab');
        
        numeroProcessoInput.addEventListener('input', () => {
          const valor = numeroProcessoInput.value.replace(/\D/g, '');
          const formato = valor.replace(/(\d{7})(\d{2})(\d{4})(\d{1})/, '$1-$2.$3-$4');
          numeroProcessoInput.value = formato;
        });
        
        numeroOabInput.addEventListener('input', () => {
          const valor = numeroOabInput.value.replace(/\D/g, '');
          const formato = valor.replace(/(\d{6})(\d{1})(\d{4})/, '$1-$2-$3');
          numeroOabInput.value = formato;
        });
