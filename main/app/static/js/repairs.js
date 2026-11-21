document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('modalRemoveRepair');
    const modalRepairId = document.getElementById('modalRepairId');
    const modalEquipmentNumber = document.getElementById('modalEquipmentNumber');
    const modalTechnician = document.getElementById('modalTechnician');
    const buttons = document.querySelectorAll('.btn-remove-repair');

    if (modal && buttons.length > 0) {
        buttons.forEach(button => {
            button.addEventListener('click', function() {
                const repairId = this.getAttribute('data-id');
                const equipment = this.getAttribute('data-equipment');
                const technicianId = this.getAttribute('data-technician');
                
                modalRepairId.value = repairId;
                modalEquipmentNumber.value = equipment;
                
                if (technicianId) {
                    modalTechnician.value = technicianId;
                }
                
                modal.showModal();
            });
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.close();
            }
        });
    }
});