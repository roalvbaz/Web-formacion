const form = document.getElementById('cuestionario-appcc');
const status = document.getElementById('form-status');
const messageBox = document.getElementById('mensaje-exito');
const messageText = document.getElementById('message-text');
const revealButton = document.getElementById('show-form-button');
const formCard = document.getElementById('form-card');

const correctAnswers = {
  p1: 'e',
  p2: 'b',
  p3: 'd',
  p4: 'e',
  p5: 'c',
  p6a: 'fisico',
  p6b: 'biologico',
  p6c: 'quimico',
  p6d: 'quimico',
  p7: 'c',
  p8: 'b',
  p9: 'a',
  p10: 'd',
  p11: 'd',
  p12: 'd',
  p13: 'f',
  p14: 'v',
  p15: 'f',
  p16: 'v',
  p17: 'v',
  p18: 'v',
  p19: 'v',
  p20: 'f',
  p21: 'f',
  p22: 'f',
  p23: 'v',
  p24: 'f',
  p25: 'v',
  p26: 'v'
};

function showMessage(type, text) {
  messageBox.className = `message ${type}`;
  messageText.textContent = text;
}

if (revealButton && formCard) {
  revealButton.addEventListener('click', function () {
    formCard.hidden = false;
    formCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

if (form) {
  form.addEventListener('submit', async function (event) {
    event.preventDefault();

    const data = new FormData(form);
    const answers = Object.fromEntries(data.entries());
    const name = answers.nombre?.toString().trim() || 'participante';

    let score = 0;
    Object.entries(correctAnswers).forEach(([question, correctAnswer]) => {
      const selected = answers[question];
      if (selected === correctAnswer) {
        score += 1;
      }
    });

    const requiredQuestions = Object.keys(correctAnswers);
    const answeredAll = requiredQuestions.every((question) => Boolean(answers[question]));

    if (!answers.nombre || !answers.dni || !answers.email || !answers.centro || !answeredAll) {
      status.textContent = 'Completa todos los datos obligatorios y responde a todas las preguntas.';
      showMessage('error', 'No puedes enviar el cuestionario incompleto.');
      return;
    }

    if (score > 14) {
      const payload = {
        nombre: answers.nombre,
        dni: answers.dni,
        email: answers.email,
        centro: answers.centro,
        score,
        respuestas: answers,
        fecha: new Date().toISOString()
      };

      try {
        const response = await fetch('/api/registro', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.error || 'No se pudo guardar el registro');
        }

        status.textContent = `Aprobado con ${score} aciertos. El registro ha quedado guardado.`;
        showMessage('success', `¡Enhorabuena, ${name}! Has aprobado con ${score} aciertos y tu registro se ha guardado en la base de datos.`);
        form.reset();
      } catch (error) {
        status.textContent = error.message;
        showMessage('error', error.message);
      }
    } else {
      formCard.hidden = true;
      alert(`No has superado el mínimo de aciertos. Has acertado ${score} de 26 preguntas. Vuelve a leer el PDF para intentarlo de nuevo.`);
      status.textContent = `Has obtenido ${score} aciertos. Debes superar 14 para poder guardar el registro. Vuelve a leer el PDF y pulsa “He leído el PDF”.`;
      showMessage('error', `No has superado el mínimo. Has acertado ${score} de 26 preguntas. Vuelve a leer el PDF para intentarlo de nuevo.`);
      form.reset();
    }
  });
}
