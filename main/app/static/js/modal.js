document.addEventListener('DOMContentLoaded', () => {
    const modalMove = document.getElementById('modalMove');
    const modalWriteOff = document.getElementById('modalWriteOff');
    const modalRepair = document.getElementById('modalRepair');

    const btnMove = document.getElementById('btnMove');
    const btnWriteOff = document.getElementById('btnWriteOff');
    const btnRepair = document.getElementById('btnRepair');

    if (btnMove && modalMove) {
        btnMove.addEventListener('click', () => modalMove.showModal());
    }
    if (btnWriteOff && modalWriteOff) {
        btnWriteOff.addEventListener('click', () => modalWriteOff.showModal());
    }
    if (btnRepair && modalRepair) {
        btnRepair.addEventListener('click', () => modalRepair.showModal());
    }

    const modals = [modalMove, modalWriteOff, modalRepair];
    modals.forEach(modal => {
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.close();
                }
            });
        }
    });
});